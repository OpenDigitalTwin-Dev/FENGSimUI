#ifndef ELBOWSDOCKWIDGET_H
#define ELBOWSDOCKWIDGET_H

#include <QDockWidget>
#include <QVTKOpenGLWidget.h>  // 添加 QVTKOpenGLWidget
#include <vtkSmartPointer.h>
#include <vtkRenderer.h>
#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkUnstructuredGridReader.h>
#include <vtkDataSetMapper.h>
#include <vtkActor.h>

#include "MainWindow.h"
#include "Mesh/MeshThread1.h"
#include "Visual/VTKWidget.h"

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
    void TypeChanged(const QString& newType);
    void timeStepChanged(int timeStep);

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

    //void onVTKClicked();
    //void onDataTypeChanged(int index);
    void onDataTypeChanged();
    void onVTKGroupClicked();
    void onTimeStepChanged();
    void initializeTimeStepComboBox(const QStringList& fileNames);

    void onpreFrameClicked();
    void onnextFrameClicked();
    void onfirstFrameClicked();
    void onlastFrameClicked();
    void onplayForwardClicked();
    void onplayBackwardClicked();

    void onVTKlastClicked();


private:
    Ui::ElbowsDockWidget *ui;
    void initializeMaterialMap();
    void updateMaterialFile();
    QString currentWorkDir_;  // 当前的全局工作目录
    MainWindow* mainWindow;
    MeshThread1* mth1;
    MeshModule* meshModule;
    QStringList fileNames;  // 用于存储文件列表
    QString newType_;
    int timeStep;
};


#endif // ELBOWSDOCKWIDGET_H
