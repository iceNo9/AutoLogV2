# AutoLogV2

0、不要省略任意细节，所有消息使用json
1、cmd.py和ui.py和fo.py和main.py在项目A，slave.py在项目B。每个py中都使用多线程，项目A和B在同一台主机上运行
2、cmd.py和ui.py和fo.py中各自使用线程运行一个消息队列
3、main.py中使用多线程运行cmd.py和ui.py和fo.py
4、cmd.py内有2个线程，第一个线程和slave.py使用zmq进行通信，会收到2种消息，分别是head：connect，id：唯一标识和head：disconnect，id：唯一标识。当收到前一个消息时，会判断列表中是否存在该ID，如果不存在则将id的值加入列表，且值的状态为run，在2S后设置该ID为lost，如果存在，则重置2S定时器。当收到后一个消息时，将对应ID的状态设置为stop。
5、cmd.py的第二个线程不断读取消息队列，会收到2种消息，分别是head：open和head：close。当收到前一个消息时，通过第一个线程发送消息head：open给slave.py。当收到后一个消息时，通过第一个线程发送消息head：close给slave.py。
6、ui.py内有2个线程，第一个线程负责UI显示和状态切换，默认状态为就绪，UI界面有5条文本提示，分别是当前日志序号、当前运行状态、当前工作模式、日志说明文件、异常提示，在模块中有对应的成员变量。日志序号为数值，运行状态分为初始化和就绪和运行中，工作模式分为连续和间断，日志说明文件分为无和有，异常说明为字符串，当该值为空时不显示。UI界面有4个按钮，分别是切换工作模式，切换日志说明文件，收集日志，归纳日志。当运行状态为就绪时，按钮都可以使用，否则都无法使用。运行状态默认为初始化，工作模式默认为连续，日志说明文件默认为无，日志序号默认为0，异常说明默认为空，当运行状态为初始化时，只显示当前运行状态文本，按钮都不可以使用。当按钮切换工作模式触发时，切换工作模式状态为非当前值，当按钮切换日志说明文件触发时，切换日志说明文件为非当前值。当按钮收集日志触发时，发送消息head：button，cmd：save到cmd.py和fo.py的消息队列。当按钮归纳日志触发时，发送消息head：button，cmd：storage到fo.py的消息队列。请补充UI界面的实现细节
7、ui.py的第二个线程不断读取消息队列，会收到5种消息，分别是head：init，id：序号和head：result，cmd：save，status：success和head：result，cmd：save，status：fail和head：result，cmd：storage，status：success和head：result，cmd：storage，status：fail。当收到第一个消息时，更改日志序号的值为id的值，切换运行状态为就绪。收到第二个消息时，更改日志序号的值自加1，切换运行状态为就绪。收到第三个消息时，切换运行状态为就绪，异常说明添加文本"收集日志出现异常，请提交日志给开发者"。收到第四个消息时，切换运行状态为就绪。收到第五个消息时，切换运行状态为就绪，异常说明添加文本"归纳日志出现异常，请提交日志给开发者"。
8、fo.py内有一个初始化配置的方法和一个线程。配置使用json，其中存在以下项，分别是path_srclog：字符串型，path_savelog：字符串型，key：字符串数组，index：整数型，lastdate：日期型年月日。初始化配置时读取每一项到对应的成员变量中，然后发送消息head：init，id：index的值到ui.py的消息队列中。
9、fo.py的线程不断读取消息队列，会收到2种消息，分别是head：button，cmd：save和head：button，cmd：storage。当收到第一个消息时，等待cmd.py的列表中状态run的值数量为0时，遍历path_srclog路径下目录名和key的值中的成员相匹配的成员项，将匹配项保存到临时列表。如果存在临时列表不为空，则在path_savelog路径下新建名为当前时间年月日时分秒+"NO."+日志序号的目录，如果目录已存在则不新建。将临时列表中的成员项复制到新建的目录下，再删除原目录，最后将index的值加1，lastdate的值更新为当前日期年月日，将变更后的成员变量覆盖配置文件的同名项。如果操作成功则发送消息head：result，cmd：save，status：success到ui.py的消息队列，否则发送消息head：result，cmd：save，status：fail。收到第一个消息时，遍历path_savelog路径，将带有"NO."关键词的目录根据年月日分类到不同列表，然后在此路径下分别创建同名年月日的目录，拷贝列表成员到新建的目录下，然后删除原目录。
10、slave.py使用1个线程和2个成员变量，成员变量分别是运行状态和唯一标识，运行状态默认为open。第一个线程和cmd.py使用zmq进行通信，会收到2种消息，分别是head：open和head：close。当收到前一个消息时，如果当前状态为非open，则修改为open，当收到后一个消息时，如果当前状态为非close，则修改为close，且发送消息head：disconnect，id：唯一标识给cmd.py。当运行状态为open时，每隔0.5s发送消息head：connect，id：唯一标识给cmd.py。