#include "RivetingDockWidget.h"
#include "ui_RivetingDockWidget.h"
#include <QDebug>

RivetingDockWidget::RivetingDockWidget(QWidget *parent)
    : QDockWidget(parent), ui(new Ui::RivetingDockWidget)
{
    ui->setupUi(this);

//    // 连接按钮点击事件
//    connect(ui->pushButton_confirm, &QPushButton::clicked,
//            this, &RivetingDockWidget::onConfirmClicked);

    this->setMinimumWidth(250);  // 最小宽度
    this->setMaximumWidth(250);  // 最大宽度
    this->setMinimumHeight(600);  // 最小长度
    this->setMaximumHeight(600);  // 最大长度

 this->setWindowTitle("");  // 自定义边栏标题
}

RivetingDockWidget::~RivetingDockWidget()
{
    delete ui;
}

//void RivetingDockWidget::onConfirmClicked()
//{
//    bool ok1, ok2;
//    double radius = ui->radius->text().toDouble(&ok1);
//    double angle  = ui->angle->text().toDouble(&ok2);

//    if (!ok1 || !ok2) {
//        qDebug() << "输入无效";
//        return;
//    }

//    qDebug() << "压铆直径:" << radius << "深度:" << angle;

//    // TODO：调用 MainWindow 的建模函数或者发出信号通知
//}
