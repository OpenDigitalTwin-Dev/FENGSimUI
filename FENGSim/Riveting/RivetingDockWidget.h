#ifndef RIVETINGDOCKWIDGET_H
#define RIVETINGDOCKWIDGET_H

#include <QDockWidget>

namespace Ui {
class RivetingDockWidget;
}

class RivetingDockWidget : public QDockWidget
{
    Q_OBJECT

public:
    explicit RivetingDockWidget(QWidget *parent = nullptr);
    ~RivetingDockWidget();

//private slots:
//    void onConfirmClicked();

private:
    Ui::RivetingDockWidget *ui;
};

#endif // RIVETINGDOCKWIDGET_H
