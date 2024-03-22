import sys
import os
from enum import Enum
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
from mq_manager import mq_manager


class AppState(Enum):
    INITIALIZING = 0, "初始化"
    READY = 1, "就绪"
    RUNNING = 2, "运行中"

    def __new__(cls, value, display_name):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.display_name = display_name
        return obj

    @property
    def name_chinese(self):
        return self.display_name


class WorkMode(Enum):
    CONTINUOUS = 0, "连续"
    INTERMITTENT = 1, "间断"

    def __new__(cls, value, display_name):
        member = object.__new__(cls)
        member._value_ = value
        member.display_name = display_name
        return member

    @property
    def name_chinese(self):
        return self.display_name


class HasManualLog(Enum):
    NO = 0, "无"
    YES = 1, "有"

    def __new__(cls, value, display_name):
        member = object.__new__(cls)
        member._value_ = value
        member.display_name = display_name
        return member

    @property
    def name_chinese(self):
        return self.display_name


class UIStateManager(QObject):
    state_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.log_number = 0
        self.status = AppState.READY
        self.work_mode = WorkMode.CONTINUOUS
        self.has_manual_log = HasManualLog.NO
        self.exception_msg = ""

    def update_state(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.state_changed.emit(self.__dict__)


class ConsumerThread(QThread):
    def __init__(self, ui_state_manager, parent=None):
        super().__init__(parent)
        self.ui_state_manager = ui_state_manager

    def run(self):
        while True:
            message = mq_manager.get_ui_message()
            self.handle_message(message)

    def handle_message(self, message):
        # 分别处理不同类型的消息
        if message['receiver'] == 'ui':
            if message['head'] == 'init':
                updated_state = {'log_number': message['id'], 'status': 1}
                self.ui_state_manager.update_state(**updated_state)
            elif message['head'] == 'result':
                cmd = message['cmd']
                status = message['status']
                if cmd == 'save':
                    if status == 'success':
                        self.ui_state_manager.update_state(log_number=self.ui_state_manager.log_number + 1,
                                                           status="就绪")
                    elif status == 'fail':
                        error_message = "收集日志出现异常，八成是文件占用问题，确认下串口关闭没有"
                        self.ui_state_manager.update_state(exception_msg=error_message, status="就绪")
                elif cmd == 'storage':
                    if status == 'success':
                        self.ui_state_manager.update_state(status="就绪")
                    elif status == 'fail':
                        error_message = "归纳日志出现异常，八成是路径操作权限问题，别放系统盘"
                        self.ui_state_manager.update_state(exception_msg=error_message, status="就绪")
            elif message['head'] == 'button':
                forwarded_message = {
                    "sender": "ui",
                    "receiver": "fo",
                    "head": "Operation",
                    "cmd": message['cmd']
                }
                mq_manager.put_message(forwarded_message)


class MainWindow(QMainWindow):
    def __init__(self, ui_state_manager, parent=None):
        super().__init__(parent)
        self.ui_state_manager = ui_state_manager
        self.ui_state_manager.state_changed.connect(self.update_ui)
        self.init_ui()

        self.consumer_thread = ConsumerThread(self.ui_state_manager)
        self.consumer_thread.start()

    def init_ui(self):
        self.setWindowTitle("LogManager")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 创建并布局各标签
        self.log_number_label = QLabel("日志序号: {}".format(self.ui_state_manager.log_number))
        self.status_label = QLabel("当前运行状态: {}".format(self.ui_state_manager.status.name_chinese))
        self.work_mode_label = QLabel("当前工作模式: {}".format(self.ui_state_manager.work_mode.name_chinese))
        self.manual_log_label = QLabel(
            "日志说明文件: {}".format(self.ui_state_manager.has_manual_log.name_chinese))
        self.exception_label = QLabel(
            self.ui_state_manager.exception_msg if self.ui_state_manager.exception_msg else "")

        layout.addWidget(self.log_number_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.work_mode_label)
        layout.addWidget(self.manual_log_label)
        layout.addWidget(self.exception_label)

        # 创建并布局按钮
        self.change_mode_button = QPushButton("切换工作模式")
        self.change_manual_log_button = QPushButton("切换日志说明文件")
        self.collect_logs_button = QPushButton("收集日志")
        self.summarize_logs_button = QPushButton("归纳日志")

        self.change_mode_button.clicked.connect(self.on_mode_change_button_clicked)
        self.change_manual_log_button.clicked.connect(self.on_manual_log_change_button_clicked)
        self.collect_logs_button.clicked.connect(self.on_collect_logs_button_clicked)
        self.summarize_logs_button.clicked.connect(self.on_summarize_logs_button_clicked)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.change_mode_button)
        buttons_layout.addWidget(self.change_manual_log_button)
        buttons_layout.addWidget(self.collect_logs_button)
        buttons_layout.addWidget(self.summarize_logs_button)

        layout.addLayout(buttons_layout)

        # 根据初始状态禁用按钮
        self.disable_buttons_if_not_ready()

    def disable_buttons_if_not_ready(self):
        if self.ui_state_manager.status != "就绪":
            self.change_mode_button.setEnabled(False)
            self.change_manual_log_button.setEnabled(False)
            self.collect_logs_button.setEnabled(False)
            self.summarize_logs_button.setEnabled(False)

    def on_mode_change_button_clicked(self):
        # 获取当前工作模式的枚举值
        current_mode = self.ui_state_manager.work_mode
        # 根据当前模式切换到另一种模式
        new_mode = WorkMode.INTERMITTENT if current_mode == WorkMode.CONTINUOUS else WorkMode.CONTINUOUS
        # 更新状态并发送消息到消息队列
        self.ui_state_manager.update_state(work_mode=new_mode.value)

    def update_ui(self, state_dict):
        # 更新日志序号
        self.log_number_label.setText("日志序号: {}".format(state_dict['log_number']))

        # 更新运行状态标签
        status = AppState(state_dict['status'])
        self.status_label.setText("当前运行状态: {}".format(status.name_chinese))

        # 更新工作模式标签
        work_mode_value = state_dict['work_mode']
        work_mode = next((wm for wm in WorkMode if wm.value == work_mode_value), None)
        if work_mode:
            self.work_mode_label.setText("当前工作模式: {}".format(work_mode.name_chinese))

        # 更新手动日志标签
        manual_log_status = HasManualLog(state_dict['has_manual_log']).name_chinese
        self.manual_log_label.setText("日志说明文件: {}".format(manual_log_status))

        # 更新错误提示
        exception_msg = state_dict['exception_msg'] if 'exception_msg' in state_dict else ""
        self.exception_label.setText(exception_msg)

        # 根据新的运行状态更新按钮的可用性
        self.enable_or_disable_buttons(state_dict['status'])

    def enable_or_disable_buttons(self, status):
        if status == "就绪":
            self.change_mode_button.setEnabled(True)
            self.change_manual_log_button.setEnabled(True)
            self.collect_logs_button.setEnabled(True)
            self.summarize_logs_button.setEnabled(True)
        else:
            self.disable_buttons_if_not_ready()

    def on_mode_change_button_clicked(self):
        # 获取当前工作模式的枚举值
        current_mode = self.ui_state_manager.work_mode
        # 切换到另一种模式
        new_mode = WorkMode.INTERMITTENT if current_mode == WorkMode.CONTINUOUS else WorkMode.CONTINUOUS
        # 更新UI状态并发送消息到消息队列
        self.ui_state_manager.update_state(work_mode=new_mode)

    def on_manual_log_change_button_clicked(self):
        # 切换日志说明文件并发送消息到消息队列
        new_manual_log_status = not self.ui_state_manager.has_manual_log
        self.ui_state_manager.update_state(has_manual_log=new_manual_log_status)
        button_message = {
            "sender": "ui",
            "receiver": "ui",
            "head": "button",
            "cmd": "change_manual_log"
        }
        mq_manager.put_message(button_message)

    def on_collect_logs_button_clicked(self):
        # 收集日志并发送消息到消息队列
        button_message = {
            "sender": "ui",
            "receiver": "ui",
            "head": "button",
            "cmd": "save"
        }
        mq_manager.put_message(button_message)

    def on_summarize_logs_button_clicked(self):
        # 归纳日志并发送消息到消息队列
        self.ui_state_manager.update_state(has_manual_log=new_manual_log_status)
        button_message = {
            "sender": "ui",
            "receiver": "ui",
            "head": "button",
            "cmd": "storage"
        }
        mq_manager.put_message(button_message)


if __name__ == "__main__":
    ui_state_manager = UIStateManager()
    app = QApplication(sys.argv)
    window = MainWindow(ui_state_manager)
    window.show()
    sys.exit(app.exec_())
