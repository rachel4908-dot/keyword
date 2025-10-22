"""
네이버 순위 확인기 (by happy)
Copyright ⓒ 2025 happy. All rights reserved.
"""
 
import sys
import os
import uuid
import json
import urllib.request
import urllib.parse
import re
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextBrowser, QTextEdit,
    QMessageBox, QSpacerItem, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QIcon
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")
naver_ad_access_license = os.getenv("NAVER_AD_ACCESS_LICENSE")
naver_ad_secret_key = os.getenv("NAVER_AD_SECRET_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
UUID_FILE = "user_uuid.txt"

def get_user_id():
    if os.path.exists(UUID_FILE):
        with open(UUID_FILE, "r") as f:
            return f.read().strip()
    new_id = str(uuid.uuid4())
    with open(UUID_FILE, "w") as f:
        f.write(new_id)
    return new_id

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org") as response:
            return response.read().decode()
    except:
        return "Unknown"

class CustomTextEdit(QTextEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab and not event.modifiers():
            self.parent().focusNextChild()
        else:
            super().keyPressEvent(event)

class Worker(QThread):
    result_ready = Signal(str)
    progress_update = Signal(int, str)
    finished_all = Signal(dict)

    def __init__(self, keywords, mall_name):
        super().__init__()
        self.keywords = keywords
        self.mall_name = mall_name
        self.all_results = {}

    def get_top_ranked_product_by_mall(self, keyword, mall_name):
        encText = urllib.parse.quote(keyword)
        seen_titles = set()
        best_product = None
        for start in range(1, 1001, 100):
            url = f"https://openapi.naver.com/v1/search/shop.json?query={encText}&display=100&start={start}"
            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id", client_id)
            request.add_header("X-Naver-Client-Secret", client_secret)
            response = urllib.request.urlopen(request)
            result = json.loads(response.read())
            for idx, item in enumerate(result.get("items", []), start=1):
                if item.get("mallName") and mall_name in item["mallName"]:
                    title_clean = re.sub(r"<.*?>", "", item["title"])
                    if title_clean in seen_titles:
                        continue
                    seen_titles.add(title_clean)
                    rank = start + idx - 1
                    product = {
                        "rank": rank,
                        "title": title_clean,
                        "price": item["lprice"],
                        "link": item["link"],
                        "mallName": item["mallName"]
                    }
                    if not best_product or rank < best_product["rank"]:
                        best_product = product
        return best_product

    def run(self):
        total = len(self.keywords)
        for i, keyword in enumerate(self.keywords):
            result = self.get_top_ranked_product_by_mall(keyword, self.mall_name)
            if result:
                link_html = f'<a href="{result["link"]}" style="color:blue;">{result["link"]}</a>'
                html = (
                    f"<b>✅ {keyword}</b><br>"
                    f" - 순위: {result['rank']}위<br>"
                    f" - 상품명: {result['title']}<br>"
                    f" - 가격: {int(result['price']):,}원<br>"
                    f" - 링크: {link_html}<br><br>"
                )
                self.all_results[keyword] = result
            else:
                html = f"<b style='color:red;'>❌ {keyword} → 검색 결과 없음</b><br><br>"
                self.all_results[keyword] = "검색 결과 없음"
            percent = int(((i+1)/total)*100)
            self.result_ready.emit(html)
            self.progress_update.emit(percent, keyword)
        self.finished_all.emit(self.all_results)

def resource_path(relative_path):
    """PyInstaller 환경에서도 리소스 파일 경로를 올바르게 반환"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class RankCheckerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 순위 확인기 (by happy)")
        self.setWindowIcon(QIcon(resource_path("logo_inner.ico")))
        self.resize(780, 720)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        bold_font = QFont()
        bold_font.setBold(True)

        self.label_keywords = QLabel("검색어(최대 10개, 쉼표로 구분)")
        self.label_keywords.setFont(bold_font)
        self.input_keywords = CustomTextEdit(self)
        self.input_keywords.setFixedHeight(70)
        self.input_keywords.setPlaceholderText("예: 키보드, 마우스, 충전기")

        layout.addWidget(self.label_keywords)
        layout.addWidget(self.input_keywords)
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.label_mall = QLabel("판매처명 (예: OO스토어)")
        self.label_mall.setFont(bold_font)
        self.input_mall = QLineEdit()

        layout.addWidget(self.label_mall)
        layout.addWidget(self.input_mall)
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.button_check = QPushButton("순위 확인")
        self.button_check.setFont(bold_font)
        self.button_check.clicked.connect(self.start_check)

        layout.addWidget(self.button_check)
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.label_status = QLabel("")
        self.result_display = QTextBrowser()
        self.result_display.setOpenExternalLinks(True)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.label_status)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.result_display)

        self.setLayout(layout)

        footer = QLabel("ⓒ 2025 happy. 무단 복제 및 배포 금지. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(footer)

        self.dots = ['.', '..', '...']
        self.dot_index = 0
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.animate_status)

    def animate_status(self):
        dots = self.dots[self.dot_index]
        self.label_status.setText(f"🔄 검색 중{dots} {self.progress_bar.value()}% 완료")
        self.dot_index = (self.dot_index + 1) % len(self.dots)

    def start_check(self):
        self.keywords = [k.strip() for k in self.input_keywords.toPlainText().split(",") if k.strip()]
        self.mall_name = self.input_mall.text().strip()

        if not self.keywords or not self.mall_name:
            QMessageBox.warning(self, "입력 오류", "검색어와 판매처명을 모두 입력하세요.")
            return

        if len(self.keywords) > 10:
            QMessageBox.warning(self, "제한 초과", "검색어는 최대 10개까지 가능합니다.")
            return

        self.result_display.clear()
        self.progress_bar.setValue(0)
        self.label_status.setText("🔄 검색 중")
        self.dot_index = 0
        self.status_timer.start(300)

        self.worker = Worker(self.keywords, self.mall_name)
        self.worker.result_ready.connect(self.append_result)
        self.worker.progress_update.connect(self.update_status)
        self.worker.finished_all.connect(lambda _: self.status_timer.stop())
        self.worker.start()

    def append_result(self, html):
        self.result_display.append(html)

    def update_status(self, percent, keyword):
        self.progress_bar.setValue(percent)
        if percent == 100:
            self.status_timer.stop()
            self.label_status.setText("✅ 검색 완료")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RankCheckerApp()
    window.show()
    sys.exit(app.exec())

