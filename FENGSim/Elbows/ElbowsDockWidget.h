#ifndef ELBOWSDOCKWIDGET_H
#define ELBOWSDOCKWIDGET_H

#include <QDockWidget>

#include "MainWindow.h"
#include "Mesh/MeshThread1.h"

namespace Ui {
class ElbowsDockWidget;
}

class ElbowsDockWidget : public QDockWidget
{
    Q_OBJECT

public:
    explicit ElbowsDockWidget(QWidget *parent, MainWindow* _mainwindow);
    ~ElbowsDockWidget();


signals:
    void confirmParameters(double R_out, double R_in, double length,
                            double sleeve_t1, double sleeve_l1,
                           double sleeve_t, double sleeve_l,
                           double rotary_pos, double fixed_pos,
                           double arc_R, double arc_t, double arc_angle);
    void workDirChanged(const QString& newWorkDir);

private slots:
    void onConfirmClicked();  //参数化建模

    void onTubeMaterialChanged(const QString &material);
    void onRotaryMaterialChanged(const QString &material);
    void onFixedMaterialChanged(const QString &material);
    void onArcMaterialChanged(const QString &material);

    void onTubeClicked();

    void onNewFileClicked();
    void onOpenFileClicked();
    void onSaveFileClicked();

    void onStepClicked();
    void onGenerateMeshClicked();
    void onMeshPlot();
    void onInpClicked();


private:
    Ui::ElbowsDockWidget *ui;
    void initializeMaterialMap();
    void updateMaterialFile();
    QString currentWorkDir_;  // 当前的全局工作目录
    MainWindow* mainWindow;
    MeshThread1* mth1;
    MeshModule* meshModule;
};


#endif // ELBOWSDOCKWIDGET_H
