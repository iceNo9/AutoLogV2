import queue


class MessageQueueManager:
    def __init__(self):
        self.ui_queue = queue.Queue()
        self.fo_queue = queue.Queue()

    def put_message(self, message):
        receiver = message['receiver']
        if receiver == 'ui':
            self.ui_queue.put(message)
        elif receiver == 'fo':
            self.fo_queue.put(message)
        else:
            raise ValueError(f"Invalid receiver '{receiver}'")

    def get_ui_message(self):
        return self.ui_queue.get()

    def get_fo_message(self):
        return self.fo_queue.get()


# 创建全局消息队列管理器实例
mq_manager = MessageQueueManager()
