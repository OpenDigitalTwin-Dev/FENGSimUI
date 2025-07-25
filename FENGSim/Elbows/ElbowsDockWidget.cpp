#include "ElbowsDockWidget.h"
#include "ui_ElbowsDockWidget.h"
#include "Mesh/MeshGeneration.h"
#include "MainWindow.h"
#include <QFile>
#include <QDir>
#include <QDebug>
#include <QTabBar>
#include <QTextStream>
#include <QMap>
#include <QComboBox>
#include <QFileDialog>
#include <QMessageBox>
#include <QDoubleValidator>

#include "Mesh/MeshGeneration.h"
#include "Mesh/MeshThread1.h"
#include "GEdge.h"
#include "TopExp_Explorer.hxx"
#include "QString"

ElbowsDockWidget::ElbowsDockWidget(QWidget *parent, MainWindow* _mainwindow)
    : QDockWidget(parent), ui(new Ui::ElbowsDockWidget)
{
    ui->setupUi(this);
    this->mainWindow = _mainwindow;

    // 初始化材料映射关系
    initializeMaterialMap();

    connect(ui->pushButton_newFile, &QPushButton::clicked, this, &ElbowsDockWidget::onNewFileClicked);
    connect(ui->pushButton_openFile, &QPushButton::clicked, this, &ElbowsDockWidget::onOpenFileClicked);
    connect(ui->pushButton_saveFile, &QPushButton::clicked, this, &ElbowsDockWidget::onSaveFileClicked);



    // 连接各个材料 ComboBox 的信号到槽函数
    connect(ui->comboBox_tubeMaterial, &QComboBox::currentTextChanged,
            this, &ElbowsDockWidget::onTubeMaterialChanged);

    connect(ui->comboBox_rotaryMaterial, &QComboBox::currentTextChanged,
            this, &ElbowsDockWidget::onRotaryMaterialChanged);

    connect(ui->comboBox_fixedMaterial, &QComboBox::currentTextChanged,
            this, &ElbowsDockWidget::onFixedMaterialChanged);

    connect(ui->comboBox_arcMaterial, &QComboBox::currentTextChanged,
            this, &ElbowsDockWidget::onArcMaterialChanged);

    // 连接按钮点击事件
    connect(ui->pushButton_confirm, &QPushButton::clicked, this, &ElbowsDockWidget::onConfirmClicked);

    connect(ui->pushButton_tube, &QPushButton::clicked, this, &ElbowsDockWidget::onTubeClicked);

    connect(ui->pushButton_step, &QPushButton::clicked, this, &ElbowsDockWidget::onStepClicked);
    connect(ui->pushButton_generateMesh, &QPushButton::clicked, this, &ElbowsDockWidget::onGenerateMeshClicked);
    connect(ui->pushButton_inp, &QPushButton::clicked, this, &ElbowsDockWidget::onInpClicked);




    this->setMinimumWidth(250);  // 最小宽度
    this->setMaximumWidth(250);  // 最大宽度
    this->setMinimumHeight(550);  // 最小长度
    this->setMaximumHeight(5500);  // 最大长度

    this->setWindowTitle("");  // 自定义边栏标题
}

ElbowsDockWidget::~ElbowsDockWidget()
{
    delete ui;
}

void ElbowsDockWidget::onNewFileClicked() {
    // 1. 选择父目录
    QString parentDir = QFileDialog::getExistingDirectory(this, "选择保存目录");
    if (parentDir.isEmpty())
        return;
    currentWorkDir_ = parentDir + "/config" ;
    QDir dir;
    if (!dir.mkdir(currentWorkDir_)) {
        QMessageBox::warning(this, "错误", "无法创建工作目录！");
        return;}
    // 2. 提示成功
    QMessageBox::information(this, "新建成功", "已创建新工作目录：\n" + currentWorkDir_);

    // 发射信号，告诉外部 currentWorkDir_ 改变了
    emit workDirChanged(currentWorkDir_);
}

void ElbowsDockWidget::onOpenFileClicked() {

}

void ElbowsDockWidget::onSaveFileClicked() {

}

void ElbowsDockWidget::onConfirmClicked()
{
    bool ok[12];
        double R_out        = ui->lineEdit_Rout->text().toDouble(&ok[0]);
        double R_in         = ui->lineEdit_Rin->text().toDouble(&ok[1]);
        double length       = ui->lineEdit_Length->text().toDouble(&ok[2]);
        double sleeve_t1     = ui->lineEdit_SleeveThickness1->text().toDouble(&ok[3]);
        double sleeve_l1     = ui->lineEdit_SleeveLength1->text().toDouble(&ok[4]);
        double sleeve_t     = ui->lineEdit_SleeveThickness->text().toDouble(&ok[5]);
        double sleeve_l     = ui->lineEdit_SleeveLength->text().toDouble(&ok[6]);
        double rotary_pos   = ui->lineEdit_RotaryPos->text().toDouble(&ok[7]);
        double fixed_pos    = ui->lineEdit_FixedPos->text().toDouble(&ok[8]);
        double arc_R        = ui->lineEdit_ArcR->text().toDouble(&ok[9]);
        double arc_t        = ui->lineEdit_ArcThickness->text().toDouble(&ok[10]);
        double arc_angle    = ui->lineEdit_ArcAngle->text().toDouble(&ok[11]);

        for (int i = 0; i < 12; ++i) {
            if (!ok[i]) {
                qDebug() << "参数输入错误！";
                return;
            }
        }

        emit confirmParameters(R_out, R_in, length, sleeve_t1, sleeve_l1, sleeve_t, sleeve_l, rotary_pos, fixed_pos, arc_R, arc_t, arc_angle);
        qDebug() << "R_out:" << R_out
                     << "R_in:" << R_in
                     << "length:" << length
                     << "sleeve_thickness1:" << sleeve_t1
                     << "sleeve_length1:" << sleeve_l1
                     << "sleeve_thickness:" << sleeve_t
                     << "sleeve_length:" << sleeve_l
                     << "rotary_pos:" << rotary_pos
                     << "fixed_pos:" << fixed_pos
                     << "arc_R:" << arc_R
                     << "arc_t:" << arc_t
                     << "arc_angle:" << arc_angle;
}

// 预先定义好的中文到英文的映射
QMap<QString, QString> materialMap;

void ElbowsDockWidget::initializeMaterialMap() {
    // 初始化映射关系
    materialMap["304不锈钢"] = "AusteniticStainlessSteel";
    materialMap["铝合金"] = "AluminumCastAlloy";
    materialMap["钛合金"] = "Ti-6Al-4V";
    materialMap["黄铜"] = "Brass";
    materialMap["黄金"] = "Gold";
    materialMap["塑料"] = "Plastic";
    materialMap["刚体"] = "RigidBody";
}
// 示例实现
void ElbowsDockWidget::onTubeMaterialChanged(const QString &material) {
    qDebug() << "Tube 材料已选择：" << material;
    updateMaterialFile();  // 更新文件
}

void ElbowsDockWidget::onRotaryMaterialChanged(const QString &material) {
    qDebug() << "Rotary 套材料已选择：" << material;
    updateMaterialFile();  // 更新文件
}

void ElbowsDockWidget::onFixedMaterialChanged(const QString &material) {
    qDebug() << "固定套材料已选择：" << material;  
    updateMaterialFile();  // 更新文件
}

void ElbowsDockWidget::onArcMaterialChanged(const QString &material) {
    qDebug() << "弯管弧段材料已选择：" << material;
    updateMaterialFile();  // 更新文件
}

void ElbowsDockWidget::updateMaterialFile()
{
    // 获取每个 ComboBox 中当前选择的中文材料
        QString tubeMaterialCN = ui->comboBox_tubeMaterial->currentText();
        QString rotaryMaterialCN = ui->comboBox_rotaryMaterial->currentText();
        QString fixedMaterialCN = ui->comboBox_fixedMaterial->currentText();
        QString arcMaterialCN = ui->comboBox_arcMaterial->currentText();

        // 将中文材料名称转换为英文名称
        QString tubeMaterial = materialMap.value(tubeMaterialCN, tubeMaterialCN);  // 如果没有找到，使用中文名
        QString rotaryMaterial = materialMap.value(rotaryMaterialCN, rotaryMaterialCN);
        QString fixedMaterial = materialMap.value(fixedMaterialCN, fixedMaterialCN);
        QString arcMaterial = materialMap.value(arcMaterialCN, arcMaterialCN);

    // 假设你有一个文件夹，用来存储每个材料对应的文件
    // 这里的路径是一个假设的路径，可以根据实际情况进行修改
    QString tubeMaterialFile = "/home/ysy/FENGSim/starter/FENGSim/Elbows/materials/" + tubeMaterial + ".FCMat";
    QString rotaryMaterialFile = "/home/ysy/FENGSim/starter/FENGSim/Elbows/materials/" + rotaryMaterial + ".FCMat";
    QString fixedMaterialFile = "/home/ysy/FENGSim/starter/FENGSim/Elbows/materials/" + fixedMaterial + ".FCMat";
    QString arcMaterialFile = "/home/ysy/FENGSim/starter/FENGSim/Elbows/materials/" + arcMaterial + ".FCMat";

    // 文件路径
    QString filePath = "/home/ysy/FENGSim/starter/FENGSim/Elbows/config/material.info";

    // 打开文件
    QFile file(filePath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        qDebug() << "无法打开文件!";
        return;
    }

    QTextStream out(&file);

    // 写入材料文件路径到文件
    out << "---" << "\n";
    out << "Volume1: " << tubeMaterialFile << "\n";
    out << "Volume2: " << rotaryMaterialFile << "\n";
    out << "Volume3: " << fixedMaterialFile << "\n";
    out << "Volume4: " << arcMaterialFile << "\n";

    file.close();

    qDebug() << "材料文件路径已保存到文件：" << filePath;
}

void ElbowsDockWidget::onTubeClicked(){
    // 获取ComboBox 中当前选择的中文材料
    QString tubeMaterialCN = ui->comboBox_tubeMaterial->currentText();
    // 将中文材料名称转换为英文名称
    QString tubeMaterial = materialMap.value(tubeMaterialCN, tubeMaterialCN);
    //路径问题解决
    QString appDirPath = QCoreApplication::applicationDirPath();
    QDir dir(appDirPath);
    dir.cdUp();
    QString parentDirPath = dir.absolutePath(); //"/home/ysy/FENGSim/starter"
    // 设置图片路径
    QString imagePath1 = parentDirPath + "/FENGSim/Elbows/materials/images/" + tubeMaterial + "/1.png";
    QString imagePath2 = parentDirPath + "/FENGSim/Elbows/materials/images/" + tubeMaterial + "/2.png";
    QString imagePath3 = parentDirPath + "/FENGSim/Elbows/materials/images/" + tubeMaterial + "/3.png";
    qDebug() << "" << imagePath1;
    // 加载三张图片并显示
    QPixmap pixmap1(imagePath1);
    QPixmap pixmap2(imagePath2);
    QPixmap pixmap3(imagePath3);
    // 将加载的图片显示到 QLabel 上
    ui->label_23->setPixmap(pixmap1);
    ui->label_24->setPixmap(pixmap2);
    ui->label_25->setPixmap(pixmap3);
    // 可选：设置图片显示的尺寸，避免显示太大或太小
    ui->label_23->setScaledContents(true);
    ui->label_24->setScaledContents(true);
    ui->label_25->setScaledContents(true);
}

void ElbowsDockWidget::onGenerateMeshClicked() {
    MeshThread1* mth1 = new MeshThread1;
    mth1->S = mainWindow->parts->Union();
    mth1->size = ui->doubleSpinBox->value();
    mth1->refine_level = 0;
    mth1->path = mainWindow->meas_path;
    qDebug() << "" << mth1->size;
    //MeshModule* meshModule = new MeshModule;
    mth1->MM = &mainWindow->MM;
    ui->pushButton_generateMesh->setEnabled(false);
    mth1->start();
    connect(mth1, SIGNAL(finished()), this, SLOT(onMeshPlot()));
}
void ElbowsDockWidget::onMeshPlot(){
    ui->pushButton_generateMesh->setEnabled(true);
    mainWindow->vtk_widget->Hide();
    mainWindow->MM.FileFormat();
    mainWindow->vtk_widget->ImportVTKFile((mainWindow->meas_path+QString("/data/mesh/fengsim_mesh.vtk")).toStdString());
}

void ElbowsDockWidget::onStepClicked(){
    bool ok[5];
    double angle = ui->lineEdit_ArcAngle->text().toDouble(&ok[0]);
    double step1 = ui->init_step->text().toDouble(&ok[1]);
    double step2 = ui->all_step->text().toDouble(&ok[2]);
    double step3 = ui->min_step->text().toDouble(&ok[3]);
    double step4 = ui->max_step->text().toDouble(&ok[4]);

    double adjustedAngle = angle * 1.1;  // 增加10%

    QString output = QString("---\nangle: %1\nstep: %2, %3, %4, %5")
                    .arg(adjustedAngle, 0, 'g', 6)   // 使用'0'格式控制，'g'表示自动选择格式，6是有效数字的最大位数
                    .arg(step1, 0, 'g', 6)
                    .arg(step2, 0, 'g', 6)
                    .arg(step3, 0, 'g', 6)
                    .arg(step4, 0, 'g', 6);

    QFile file("/home/ysy/FENGSim/starter/FENGSim/Elbows/config/step.info");  // 你可以指定路径
    if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&file);
        out << output;
        file.close();
    }
}

void ElbowsDockWidget::onInpClicked(){
    // 创建 QProcess 对象
    QProcess *process = new QProcess(this);
    // 构建 Python 脚本执行的命令
    QString pythonCommand = "python3";
    QString scriptPath = "/home/ysy/FENGSim/starter/FENGSim/Elbows/config/GenerateInp.py";
    // 启动 Python 脚本
    process->start(pythonCommand, QStringList() << scriptPath);
}






