import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QStackedWidget

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('manager_pc/dogniel_manager/dogniel_manager.ui', self)  # UI 파일 경로

        # StackedWidget과 버튼 찾기
        self.stacked_widget = self.findChild(QStackedWidget, 'stackedWidget')
        self.c_Button = self.findChild(QPushButton, 'c_Button')
        self.r_Button = self.findChild(QPushButton, 'r_Button')

        # StackedWidget 초기 숨김
        self.stacked_widget.hide()

        # 상위 버튼 연결
        self.c_Button.clicked.connect(self.toggle_options1)
        self.r_Button.clicked.connect(self.toggle_options2)

        # 하위 버튼 초기 숨김
        self.verticalLayoutWidget = self.findChild(QWidget, 'verticalLayoutWidget')
        self.verticalLayoutWidget_2 = self.findChild(QWidget, 'verticalLayoutWidget_2')

        # 하위 버튼을 숨깁니다.
        self.hide_sub_buttons(self.verticalLayoutWidget)
        self.hide_sub_buttons(self.verticalLayoutWidget_2)

        # 하위 버튼 연결
        self.c1_Button = self.findChild(QPushButton, 'c1_Button')
        self.c2_Button = self.findChild(QPushButton, 'c2_Button')
        self.c3_Button = self.findChild(QPushButton, 'c3_Button')

        self.c1_Button.clicked.connect(lambda: self.go_to_page(0))  # Page 1
        self.c2_Button.clicked.connect(lambda: self.go_to_page(1))  # Page 2
        self.c3_Button.clicked.connect(lambda: self.go_to_page(2))  # Page 3

        self.r1_Button.clicked.connect(lambda: self.go_to_page(3))  # Page 4
        self.r2_Button.clicked.connect(lambda: self.go_to_page(4))  # Page 5
    def hide_sub_buttons(self, widget):
        if widget is not None:
            widget.hide()  # 전체 위젯 숨김
            for button in widget.findChildren(QPushButton):
                button.hide()  # 하위 버튼 숨김

    def toggle_options1(self):
        if self.verticalLayoutWidget.isVisible():
            self.hide_sub_buttons(self.verticalLayoutWidget)
        else:
            self.verticalLayoutWidget.show()  # 하위 버튼 표시
            for button in self.verticalLayoutWidget.findChildren(QPushButton):
                button.show()
            self.stacked_widget.show()  # StackedWidget 표시

    def toggle_options2(self):
        if self.verticalLayoutWidget_2.isVisible():
            self.hide_sub_buttons(self.verticalLayoutWidget_2)
        else:
            self.verticalLayoutWidget_2.show()  # 하위 버튼 표시
            for button in self.verticalLayoutWidget_2.findChildren(QPushButton):
                button.show()
            self.stacked_widget.show()  # StackedWidget 표시

    def go_to_page(self, index):
        self.stacked_widget.setCurrentIndex(index)  # 선택된 페이지로 전환

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_app = MyApp()
    my_app.show()
    sys.exit(app.exec_())
