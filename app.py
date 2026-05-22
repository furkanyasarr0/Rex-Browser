import sys
from PyQt6.QtCore import QUrl, pyqtSignal, Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLineEdit, QToolBar, 
                             QTabWidget, QDialog, QVBoxLayout, QFormLayout, 
                             QPushButton, QComboBox, QMessageBox, QCheckBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None, dns_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Tarayıcı Ayarları")
        self.setFixedSize(350, 200)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # DNS Checkbox - Cloudflare entegrasyonu için arayüz
        self.dns_checkbox = QCheckBox("Cloudflare DNS (1.1.1.1) Kullan")
        self.dns_checkbox.setChecked(dns_enabled)
        form_layout.addRow("Ağ Ayarları:", self.dns_checkbox)
        
        self.homepage_input = QLineEdit()
        self.homepage_input.setText("https://www.google.com")
        form_layout.addRow("Varsayılan Ana Sayfa:", self.homepage_input)
        
        self.search_engine = QComboBox()
        self.search_engine.addItems(["Google", "DuckDuckGo", "Bing", "Yahoo"])
        form_layout.addRow("Varsayılan Arama Motoru:", self.search_engine)
        
        layout.addLayout(form_layout)
        save_btn = QPushButton("Ayarları Kaydet")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)

    def is_dns_enabled(self):
        return self.dns_checkbox.isChecked()

class CustomWebEngineView(QWebEngineView):
    def createWindow(self, _type):
        # Yeni pencere isteklerini ana pencere üzerinde yeni sekme olarak aç
        if hasattr(self.parent(), "add_new_tab"):
            return self.parent().add_new_tab().page()
        return super().createWindow(_type)

class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Ayarları sistemden kalıcı olarak yükle
        self.settings = QSettings("Wacpy", "BrowserSettings")
        self.use_cloudflare_dns = self.settings.value("use_cloudflare_dns", True, type=bool)
        
        self.setMinimumSize(800, 600)
        
        # --- KİMLİK (USER-AGENT) ---
        profile = QWebEngineProfile.defaultProfile()
        modern_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        profile.setHttpUserAgent(modern_user_agent)
        
        # Sekme Yöneticisi
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True) 
        self.tabs.setStyleSheet("QTabBar::tab { width: 180px; text-align: left; }")
        
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True) 
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        
        self.setCentralWidget(self.tabs)
        
        navbar = QToolBar()
        navbar.setMovable(False)
        self.addToolBar(navbar)
        
        back_btn = QAction('◀️', self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navbar.addAction(back_btn)
        
        forward_btn = QAction('▶️', self)
        forward_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navbar.addAction(forward_btn)
        
        reload_btn = QAction('🔄️', self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navbar.addAction(reload_btn)
        
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)
        
        # Çerez Temizleme Butonu
        cookie_btn = QAction('🍪', self)
        cookie_btn.setToolTip("Tüm Çerezleri Temizle")
        cookie_btn.triggered.connect(self.clear_cookies_popup)
        navbar.addAction(cookie_btn)
        
        bookmark_btn = QAction('⭐', self)
        bookmark_btn.setToolTip("Bu sayfayı favorilere ekle")
        bookmark_btn.triggered.connect(self.add_current_page_to_bookmarks)
        navbar.addAction(bookmark_btn)
        
        settings_btn = QAction('⚙️', self)
        settings_btn.setToolTip("Tarayıcı Ayarları")
        settings_btn.triggered.connect(self.open_settings)
        navbar.addAction(settings_btn)
        
        # Yer İmleri
        self.bookmarks = [{"name": "Google", "url": "https://www.google.com"}]
        self.addToolBarBreak() 
        self.bookmarks_bar = QToolBar("Yer İmleri")
        self.bookmarks_bar.setMovable(False)
        self.bookmarks_bar.setVisible(False)
        self.addToolBar(self.bookmarks_bar)
        self.render_bookmarks()
        
        # Kısayollar
        self.shortcut_new_window = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_new_window.activated.connect(self.open_new_window)
        
        self.shortcut_close_tab = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut_close_tab.activated.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))
        
        self.shortcut_toggle_bookmarks = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut_toggle_bookmarks.activated.connect(self.toggle_bookmarks)

        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(lambda: self.tabs.currentWidget().reload() if self.tabs.currentWidget() else None)
        QShortcut(QKeySequence("F5"), self).activated.connect(lambda: self.tabs.currentWidget().reload() if self.tabs.currentWidget() else None)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.add_current_page_to_bookmarks)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.focus_url_bar)
        QShortcut(QKeySequence("Alt+Left"), self).activated.connect(lambda: self.tabs.currentWidget().back() if self.tabs.currentWidget() else None)
        QShortcut(QKeySequence("Alt+Right"), self).activated.connect(lambda: self.tabs.currentWidget().forward() if self.tabs.currentWidget() else None)
        QShortcut(QKeySequence("F11"), self).activated.connect(self.toggle_fullscreen)
        
        # Yakınlaştırma (Zoom) Kısayolları
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self.zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self.zoom_reset)
        
        # Sekmeler arası geçiş
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self.prev_tab)

        self.add_new_tab(QUrl("https://www.google.com"), "Google")

    def clear_cookies_popup(self):
        reply = QMessageBox.question(self, 'Çerezleri Temizle', 
                                     "Tüm çerezleri silmek istediğinize emin misiniz?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            QWebEngineProfile.defaultProfile().cookieStore().deleteAllCookies()
            QMessageBox.information(self, "Bilgi", "Çerezler silindi.")

    def add_new_tab(self, qurl=None, label="Yeni Sekme"):
        if qurl is None or isinstance(qurl, bool): qurl = QUrl("https://www.google.com")
        browser = CustomWebEngineView(self)
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(b, title))
        browser.urlChanged.connect(lambda qurl, b=browser: self.update_urlbar(qurl, b))
        
        return browser

    def update_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index != -1:
            display_title = (title[:17] + "...") if len(title) > 20 else title
            self.tabs.setTabText(index, display_title)

    def tab_open_doubleclick(self, i):
        if i == -1: self.add_new_tab()

    def current_tab_changed(self, i):
        if self.tabs.currentWidget():
            self.update_urlbar(self.tabs.currentWidget().url(), self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)

    def open_new_window(self):
        new_win = CustomBrowser()
        new_win.showMaximized()

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith('http'): url = 'https://' + url
        self.tabs.currentWidget().setUrl(QUrl(url))

    def update_urlbar(self, q, browser=None):
        if browser != self.tabs.currentWidget(): return
        self.url_bar.setText(q.toString())

    def toggle_bookmarks(self):
        self.bookmarks_bar.setVisible(not self.bookmarks_bar.isVisible())

    def open_settings(self):
        dialog = SettingsDialog(self, dns_enabled=self.use_cloudflare_dns)
        if dialog.exec():
            yeni_dns_durumu = dialog.is_dns_enabled()
            
            # Sadece ayar değiştiyse kaydet ve yeniden başlatma uyarısı ver
            if yeni_dns_durumu != self.use_cloudflare_dns:
                self.use_cloudflare_dns = yeni_dns_durumu
                self.settings.setValue("use_cloudflare_dns", self.use_cloudflare_dns)
                
                QMessageBox.information(self, "Yeniden Başlatma Gerekli", 
                                        "DNS tercihiniz kaydedildi.\nAyarların aktif olabilmesi için tarayıcıyı kapatıp yeniden açmanız gerekmektedir.")

    def add_current_page_to_bookmarks(self):
        current_browser = self.tabs.currentWidget()
        url = current_browser.url().toString()
        title = current_browser.page().title() or "Yeni Sayfa"
        if not any(b["url"] == url for b in self.bookmarks):
            self.bookmarks.append({"name": title[:10], "url": url})
            self.render_bookmarks()

    def render_bookmarks(self):
        self.bookmarks_bar.clear()
        for b in self.bookmarks:
            btn = QAction(b["name"], self)
            btn.triggered.connect(lambda _, u=b["url"]: self.tabs.currentWidget().setUrl(QUrl(u)))
            self.bookmarks_bar.addAction(btn)

    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def zoom_in(self):
        if self.tabs.currentWidget():
            current_zoom = self.tabs.currentWidget().zoomFactor()
            self.tabs.currentWidget().setZoomFactor(current_zoom + 0.1)

    def zoom_out(self):
        if self.tabs.currentWidget():
            current_zoom = self.tabs.currentWidget().zoomFactor()
            self.tabs.currentWidget().setZoomFactor(max(0.25, current_zoom - 0.1)) # Çok fazla küçülmesini engeller

    def zoom_reset(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setZoomFactor(1.0)

    def next_tab(self):
        if self.tabs.count() > 1:
            idx = (self.tabs.currentIndex() + 1) % self.tabs.count()
            self.tabs.setCurrentIndex(idx)

    def prev_tab(self):
        if self.tabs.count() > 1:
            idx = (self.tabs.currentIndex() - 1) % self.tabs.count()
            self.tabs.setCurrentIndex(idx)

if __name__ == "__main__":
    # Uygulama motoru başlamadan önce kullanıcının DNS tercihini okuyoruz
    temp_settings = QSettings("Wacpy", "BrowserSettings")
    is_dns_active = temp_settings.value("use_cloudflare_dns", True, type=bool)
    
    if is_dns_active:
        # Cloudflare DNS (DoH) Aktif
        sys.argv.append("--enable-features=DNSOverHttps")
        sys.argv.append("--dns-over-https-mode=automatic")
        sys.argv.append("--dns-over-https-templates=https://1.1.1.1/dns-query")
    else:
        # Sistem DNS'ine dön (DoH Kapalı)
        sys.argv.append("--disable-features=DNSOverHttps")
    
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Wacpy Browser")
    
    # Yüksek DPI ayarı
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    # GPU Hızlandırma parametreleri
    sys.argv.append("--enable-gpu-rasterization")
    sys.argv.append("--ignore-gpu-blocklist")
    
    window = CustomBrowser()
    window.setWindowState(Qt.WindowState.WindowMaximized)
    window.show()
    
    sys.exit(app.exec())