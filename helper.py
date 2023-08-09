import sys
import json
import time
import sched
from uuid import uuid1
from plyer import notification
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMainWindow, QApplication, QCompleter, QComboBox,\
     QTabWidget, QLabel, QWidget, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon, QRegExpValidator
from PyQt5.QtCore import QSortFilterProxyModel, Qt, pyqtSignal, QRect, QMetaObject,\
     QCoreApplication, pyqtSlot, QThread, QRegExp



# 选择控件
class ExtendedComboBox(QComboBox):
    def __init__(self, parent=None):
        super(ExtendedComboBox, self).__init__(parent)
        self.setEditable(True)
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())
        self.completer = QCompleter(self.pFilterModel, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)
        self.completer.activated.connect(self.on_completer_activated)

    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)

    def setModel(self, model):
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Enter & e.key() == Qt.Key_Return:
            text = self.currentText()
            index = self.findText(text, Qt.MatchExactly | Qt.MatchCaseSensitive)
            self.setCurrentIndex(index)
            self.hidePopup()
            super(ExtendedComboBox, self).keyPressEvent(e)
        else:
            super(ExtendedComboBox, self).keyPressEvent(e)


# 主窗口
class MainWindow(QMainWindow):
    def __init__(self):
        # print("初始化系统")
        # print("当前活跃线程数量为", threading.active_count())
        # print("当前所有线程信息", threading.enumerate())
        # print("当前线程信息", threading.current_thread())
        # print("==========================")
        super(MainWindow, self).__init__(None)
        self.to_do_json_path = "./todo.json"
        self.to_do_dict = {"提醒":[]}
        self.to_do_list = list()
        self.remind_thread = None
        self.setupUi()
        # 读取json到字典再到table控件
        self.load_json_to_dict()
        self.load_dict_to_table()
        #　启动后台提醒线程
        if 0 < len(self.to_do_list):
            self.start_remind_thread(self.to_do_list[0])

    # 初始化控件
    def setupUi(self):
        self.setWindowTitle("私人助手")
        self.setWindowIcon(QIcon("./logo.ico"))
        self.resize(680, 520)
        self.setTabShape(QTabWidget.Rounded)
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        # 第一排
        self.label_action = QLabel(self.central_widget)
        self.label_action.setGeometry(QRect(10, 13, 54, 12))
        self.label_action.setObjectName("label_action")
        self.combo_box_action = ExtendedComboBox(self.central_widget)
        self.combo_box_action.setGeometry(QRect(70, 10, 250, 20))
        self.combo_box_action.setObjectName("combo_box_action")
        self.combo_box_action.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_box_action.addItem("提醒")
        self.combo_box_action.addItem("脚本")
        self.label_loop = QLabel(self.central_widget)
        self.label_loop.setGeometry(QRect(360, 13, 54, 12))
        self.label_loop.setObjectName("label_loop")
        self.combo_box_loop = ExtendedComboBox(self.central_widget)
        self.combo_box_loop.setGeometry(QRect(420, 10, 250, 20))
        self.combo_box_loop.setObjectName("combo_box_loop")
        self.combo_box_loop.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_box_loop.addItem("单次")
        self.combo_box_loop.addItem("每天")
        self.combo_box_loop.addItem("每周")
        self.combo_box_loop.addItem("每两周")
        # 第二排
        current_time = datetime.now()
        self.label_date = QLabel(self.central_widget)
        self.label_date.setGeometry(QRect(10, 42, 48, 16))
        self.label_date.setObjectName("label_date")
        self.line_edit_date = QLineEdit(self.central_widget)
        self.line_edit_date.setGeometry(QRect(70, 40, 250, 20))
        self.line_edit_date.setObjectName("line_edit_date")
        self.line_edit_date.setText(f"{current_time.year}-{current_time.month:02d}-{current_time.day:02d}")
        # self.line_edit_date.setPlaceholderText("2023-08-01")
        re_date = QRegExp(r"^(\d{4}-\d{2}-\d{2})$")
        re_validator_date = QRegExpValidator(re_date, self)
        self.line_edit_date.setValidator(re_validator_date)
        self.label_clock = QLabel(self.central_widget)
        self.label_clock.setGeometry(QRect(360, 42, 48, 16))
        self.label_clock.setObjectName("label_date")
        self.line_edit_clock = QLineEdit(self.central_widget)
        self.line_edit_clock.setGeometry(QRect(420, 40, 250, 20))
        self.line_edit_clock.setObjectName("line_edit_clock")
        # self.line_edit_clock.setPlaceholderText("00:00:00")
        self.line_edit_clock.setText(f"{current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}")
        re_clock = QRegExp(r"^(\d{2}:\d{2}:\d{2})$")
        re_validator_clock = QRegExpValidator(re_clock, self)
        self.line_edit_clock.setValidator(re_validator_clock)
        # 第三排
        self.label_remind_title = QLabel(self.central_widget)
        self.label_remind_title.setGeometry(QRect(10, 71, 48, 16))
        self.label_remind_title.setObjectName("label_remind_title")
        self.line_edit_title = QLineEdit(self.central_widget)
        self.line_edit_title.setGeometry(QRect(70, 68, 250, 20))
        self.line_edit_title.setObjectName("line_edit_title")
        self.line_edit_title.setPlaceholderText("请输入标题(必填)")
        self.label_remind_context = QLabel(self.central_widget)
        self.label_remind_context.setGeometry(QRect(360, 71, 48, 16))
        self.label_remind_context.setObjectName("label_remind_context")
        self.line_edit_context = QLineEdit(self.central_widget)
        self.line_edit_context.setGeometry(QRect(420, 68, 250, 20))
        self.line_edit_context.setObjectName("line_edit_context")
        self.line_edit_context.setPlaceholderText("请输入内容(选填)")
        # 第四排
        self.push_button_add = QPushButton(self.central_widget)
        self.push_button_add.setGeometry(QRect(10, 96, 662, 25))
        self.push_button_add.setObjectName("push_button_add")
        # 第五排
        self.label_table_title = QLabel(self.central_widget)
        self.label_table_title.setGeometry(QRect(10, 150, 48, 16))
        self.label_table_title.setObjectName("label_table_title")
        self.table_show = QTableWidget(self.central_widget)
        self.table_show.setColumnCount(7)
        self.table_show.setHorizontalHeaderLabels(["日期", "时间", "周期", "动作", "标题", "内容", "操作"])
        self.table_show.setGeometry(QRect(10, 170, 660, 310))
        self.table_show.setColumnWidth(0, 72)
        self.table_show.setColumnWidth(1, 57)
        self.table_show.setColumnWidth(2, 50)
        self.table_show.setColumnWidth(3, 35)
        self.table_show.setColumnWidth(4, 80)
        self.table_show.setColumnWidth(5, 309)
        self.table_show.setColumnWidth(6, 40)
        self.table_show.setColumnWidth(7, 1)
        self.table_show.setShowGrid(False)
        self.table_show.setObjectName("table_show")
        # 设置大小
        self.setCentralWidget(self.central_widget)
        self.setFixedSize(self.width(), self.height())
        self.retranslateUi()
        QMetaObject.connectSlotsByName(self)

    # 初始化控件提示
    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.setWindowIcon(QIcon(":/icon/logo.ico"))
        self.setWindowTitle(_translate("MainWindow", "私人助手"))
        # 第一排
        self.label_action.setText(_translate("mainWindow", "动    作"))
        self.label_loop.setText(_translate("mainWindow", "模    式"))
        # 第二排
        self.label_date.setText(_translate("mainWindow", "日    期"))
        self.label_clock.setText(_translate("mainWindow", "时    间"))
        # 第三排
        self.label_remind_title.setText(_translate("mainWindow", "标    题"))
        self.label_remind_context.setText(_translate("mainWindow", "内    容"))
        # 第四排
        self.push_button_add.setText(_translate("mainWindow", "增加并启用"))
        # 第五排
        self.label_table_title.setText(_translate("mainWindow", "待办事项"))

    # 读取json到字典，并将待办事项加入内存字典
    def load_json_to_dict(self):
        self.to_do_dict = {"提醒":[]}
        raw_json = None
        with open(self.to_do_json_path, 'r', encoding='utf-8') as file:
            raw_json = json.load(file)
        to_del_list = list()
        # 处理"提醒"中的"单次"事项
        for index,item in enumerate(raw_json.get("提醒")):
            if "单次" == item.get("周期"):
                remind_time = time.mktime(time.strptime(f"{item.get('日期')} {item.get('时间')}", "%Y-%m-%d %H:%M:%S"))
                current_time = time.time()
                if current_time <= remind_time:
                    self.to_do_dict[item.get("动作")].append(item)
                else:
                    # 记录需要删除的过期提醒
                    to_del_list.append(item)
            else:
                item["日期"] = self.modify_loop_remind_date(f"{item.get('日期')} {item.get('时间')}", item.get('周期'))
                current_time = datetime.now()
                remind_time = datetime.strptime(f"{item.get('日期')} {item.get('时间')}", "%Y-%m-%d %H:%M:%S")
                self.to_do_dict["提醒"].append(item)
                # 删除json文件中循环提醒的日期
                raw_json["提醒"][index]["日期"] = item.get("日期")
        # 删除json文件中过期的提醒
        for item in to_del_list:
            raw_json[item.get("动作")].remove(item)
        with open(self.to_do_json_path, 'w', encoding='utf-8') as file:
            json.dump(raw_json, file, ensure_ascii=False, indent=4)

    # 给出循环提醒的正确日期
    def modify_loop_remind_date(self, time_str, loop_type):
        loop_days = 0
        if "每天" == loop_type:
            loop_days = 1
        elif "每周" == loop_type:
            loop_days = 7
        elif "每两周" == loop_type:
            loop_days = 14
        else:
            loop_days = 0
        current_time = datetime.now()
        given_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        while given_time < current_time:
            given_time = given_time + timedelta(days=loop_days)
        return given_time.strftime("%Y-%m-%d %H:%M:%S").split(' ')[0]

    # 读取字典, 排序后展示到列表控件
    def load_dict_to_table(self):
        self.to_do_list = list()
        # 处理"提醒"中的"单次"事项
        for item in self.to_do_dict.get("提醒"):
            self.to_do_list.append(item)
        self.to_do_list = sorted(self.to_do_list, key=lambda item:(item.get("日期"), item.get("时间")))
        for row_index, item in enumerate(self.to_do_list):
            self.table_show.insertRow(row_index)
            self.table_show.setItem(row_index, 0, QTableWidgetItem(str(item.get("日期"))))
            self.table_show.setItem(row_index, 1, QTableWidgetItem(str(item.get("时间"))))
            self.table_show.setItem(row_index, 2, QTableWidgetItem(str(item.get("周期"))))
            self.table_show.setItem(row_index, 3, QTableWidgetItem(str(item.get("动作"))))
            self.table_show.setItem(row_index, 4, QTableWidgetItem(str(item.get("标题"))))
            self.table_show.setItem(row_index, 5, QTableWidgetItem(str(item.get("内容"))))
            table_delete_button = QPushButton("删除")
            table_delete_button.clicked.connect(self.delete_table_row)
            self.table_show.setCellWidget(row_index, 6, table_delete_button)


    @pyqtSlot()
    def on_push_button_add_clicked(self):
        action = self.combo_box_action.currentText()
        loop = self.combo_box_loop.currentText()
        date = self.line_edit_date.text()
        clock = self.line_edit_clock.text()
        title = self.line_edit_title.text()
        context = self.line_edit_context.text()
        if not context: context = "未填写内容"
        remind_dict = dict()
        if action and loop and date and clock and title:
            remind_dict["ID"] = ''.join(str(uuid1()).split('-'))
            remind_dict["动作"] = action
            remind_dict["周期"] = loop
            remind_dict["日期"] = date
            remind_dict["时间"] = clock
            remind_dict["标题"] = title
            remind_dict["内容"] = context
        else:
            print("存在空数据!")
            notification.notify(title="很不幸，报错了",
                                message="填写存在空数据!",
                                timeout=20,
                                app_icon="./logo.ico")
            return
        # 修改JSON文件
        raw_json = None
        with open(self.to_do_json_path, 'r', encoding='utf-8') as file:
            raw_json = json.load(file)
        raw_json[action].append(remind_dict)
        with open(self.to_do_json_path, 'w', encoding='utf-8') as file:
            json.dump(raw_json, file, ensure_ascii=False, indent=4)
        # 读取json到字典再到table控件
        self.load_json_to_dict()
        self.table_show.clearContents()
        self.table_show.setRowCount(0)
        self.load_dict_to_table()
        self.stop_remind_thread()
        if 0 < len(self.to_do_list):
            self.start_remind_thread(self.to_do_list[0])
        return

    def delete_table_row(self):
        button = self.sender()
        row = self.table_show.indexAt(button.pos()).row()
        if None == row:
            print("无法确定表格中要删除数据的行号")
            notification.notify(title="很不幸，报错了",
                                message="无法确定表格中要删除数据的行号!",
                                timeout=20,
                                app_icon="./logo.ico")
            return
        # 获取data_id，删除json文件中对应的数据，并重新加载json数据到表格控件
        data_id = self.to_do_list[row].get("ID")
        action = self.to_do_list[row].get("动作")
        # 修改JSON文件
        raw_data = None
        if data_id and action:
            with open(self.to_do_json_path, 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
            for item in raw_data.get(action):
                if data_id == item.get("ID"):
                    raw_data[action].remove(item)
                    break
            with open(self.to_do_json_path, 'w', encoding='utf-8') as file:
                json.dump(raw_data, file, ensure_ascii=False, indent=4)
        else:
            print("无法确定json文件中要删除的具体数据!")
            notification.notify(title="很不幸，报错了",
                                message="无法确定json文件中要删除的具体数据!",
                                timeout=20,
                                app_icon="./logo.ico")
            return
        # 读取json到字典再到table控件
        self.load_json_to_dict()
        self.table_show.clearContents()
        self.table_show.setRowCount(0)
        self.load_dict_to_table()
        self.stop_remind_thread()
        if 0 < len(self.to_do_list):
            self.start_remind_thread(self.to_do_list[0])
        return

    def start_remind_thread(self, remind_item):
        # 创建并启动线程线程
        self.remind_thread = RemindThread(remind_item)
        self.remind_thread.finished.connect(self.remind_finish_update_data)
        self.remind_thread.start()

    def stop_remind_thread(self):
        if self.remind_thread:
            # print("停止前队列中的事件数量:", len(self.remind_thread.scheduler.queue))
            if 0 != len(self.remind_thread.scheduler.queue):
                self.remind_thread.scheduler.cancel(self.remind_thread.event)
            # print("停止后队列中的事件数量:", len(self.remind_thread.scheduler.queue))
            self.remind_thread.terminate()

    def remind_finish_update_data(self, remind_item):
         # 判断是否进行定时, 修改json文件, 重新加载json文件到table文件
        raw_json = None
        with open(self.to_do_json_path, 'r', encoding='utf-8') as file:
            raw_json = json.load(file)
        if "单次" == remind_item.get("周期"):
            for item in raw_json[remind_item.get("动作")]:
                if remind_item.get("ID") == item.get("ID"):
                    raw_json[remind_item.get("动作")].remove(remind_item)
                with open(self.to_do_json_path, 'w', encoding='utf-8') as file:
                    json.dump(raw_json, file, ensure_ascii=False, indent=4)
        else:
            remind_item["日期"] = self.modify_loop_remind_date(f"{remind_item.get('日期')} {remind_item.get('时间')}", remind_item.get('周期'))
            for index,item in enumerate(raw_json[remind_item.get("动作")]):
                if remind_item.get("ID") == item.get("ID"):
                    raw_json[remind_item.get("动作")][index]["日期"] = remind_item["日期"]
            with open(self.to_do_json_path, 'w', encoding='utf-8') as file:
                json.dump(raw_json, file, ensure_ascii=False, indent=4)
        # 读取json到字典再到table控件
        self.load_json_to_dict()
        self.table_show.clearContents()
        self.table_show.setRowCount(0)
        self.load_dict_to_table()
        # 启动新的提醒线程
        self.stop_remind_thread()
        if 0 < len(self.to_do_list):
            self.start_remind_thread(self.to_do_list[0])
        return

    # 关闭窗口
    def closeEvent(self, event):
        super(MainWindow, self).closeEvent(event)


# 提醒线程的类
class RemindThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, remind_item):
        super(RemindThread, self).__init__()
        self.remind_item = remind_item
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.event = None

    def run(self):
        remind_time = time.mktime(time.strptime(f"{self.remind_item.get('日期')} {self.remind_item.get('时间')}", "%Y-%m-%d %H:%M:%S"))
        current_time = time.time()
        self.event = self.scheduler.enter(remind_time-current_time, 0, self.generate_remind, (self.remind_item,))
        # print("准备启动新的提醒线程")
        # print("当前活跃线程数量为", threading.active_count())
        # print("当前所有线程信息", threading.enumerate())
        # print("当前线程信息", threading.current_thread())
        # print("=====================================================")
        self.scheduler.run()
        # print("线程运行完毕")
        # print("=====================================================")

    def generate_remind(self, remind_item):
        notification.notify(title=remind_item.get("标题"),
                            message=remind_item.get("内容"),
                            timeout=20,
                            app_icon="./logo.ico")
        self.finished.emit(remind_item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())