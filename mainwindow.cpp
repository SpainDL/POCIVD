#include "mainwindow.h"
#include "ui_mainwindow.h"
//#include <QTextStream>
#include <QDebug>
#include <QThread>


#include "serial_reader_imp.h"
#include "tm_reader.h"
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <inttypes.h>
#include "tmr_utils.h"
#include <unistd.h>
#include <iostream>

QString test = "";

void errx(int exitval, const char* fmt, ...)
{
  va_list ap;

  va_start(ap, fmt);
  vfprintf(stderr, fmt, ap);

  exit(exitval);
}

void checkerr(TMR_Reader* rp, TMR_Status ret, int exitval, const char* msg)
{

  if (TMR_SUCCESS != ret)
  {
    errx(exitval, "Error %s: %s\n", msg, TMR_strerr(rp, ret));
  }

}

void callback(TMR_Reader* reader, const TMR_TagReadData* t, void* cookie);
void exceptionCallback(TMR_Reader* reader, TMR_Status error, void* cookie);


void
callback(TMR_Reader* reader, const TMR_TagReadData* t, void* cookie)
{
  std::cout << __LINE__ <<  "TAG!\n";
  char epcStr[128];
  char timeStr[128];

  TMR_bytesToHex(t->tag.epc, t->tag.epcByteCount, epcStr);
  TMR_getTimeStamp(reader, t, timeStr);

  //printf("Background read: Tag ID:%s ant:%d count:%d \n", epcStr, t->antenna, t->readCount);

  test = epcStr;
  //ui->physicianField->test;
}

void
exceptionCallback(TMR_Reader* reader, TMR_Status error, void* cookie)
{
    std::cout << __LINE__ <<  "Connecting!\n";

  if (reader->lastReportedException != error)
  {
    fprintf(stdout, "Error:%s\n", TMR_strerr(reader, error));
  }

  reader->lastReportedException = error;
}





MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    QPixmap bkgnd("/data/bin/bg.bmp");
    //bkgnd = bkgnd.scaled(this->size(), Qt::IgnoreAspectRatio);
    QPalette palette;
    palette.setBrush(QPalette::Background, bkgnd);
    //mainwindow.setPalette(palette);
    this->setPalette(palette);

    QPalette label_color;
    //sample_palette.setColor(QPalette::Window, Qt::white);
    label_color.setColor(QPalette::WindowText, Qt::white);

    ui->physicianLabel->setPalette(label_color);
    ui->patientLabel->setPalette(label_color);
    ui->resultsLabel->setPalette(label_color);
    ui->analyse->setDisabled(true);
    std::cout << __LINE__ <<  "Hello World!\n";


}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::on_clear_clicked()
{
    ui->physicianField->clear();
    ui->patientField->clear();
    ui->resultsField->clear();
    test = "";

    //block access to the analyse button
    ui->analyse->setDisabled(true);
    //rerun the rfid function

}

void MainWindow::on_analyse_clicked()
{



    QThread th;
    QSerialPort vibe;
    QSerialPort pW;
    //QSerialPort rfid;


    foreach (auto &port, QSerialPortInfo::availablePorts()) {
        qDebug() << port.portName();
    }
    // vibe serial port config
    vibe.setPortName("ttyACM0");
    vibe.setBaudRate(QSerialPort::Baud9600);
    vibe.setDataBits(QSerialPort::Data8);
    vibe.setParity(QSerialPort::NoParity);
    vibe.setStopBits(QSerialPort::OneStop);

    //PW serial port config
    pW.setPortName("ttyACM1");
    pW.setBaudRate(QSerialPort::Baud9600);
    pW.setDataBits(QSerialPort::Data8);
    pW.setParity(QSerialPort::NoParity);
    pW.setStopBits(QSerialPort::OneStop);

    //vibe.setDataTerminalReady(true);
    QString negative = "Negative";
    QString positive = "Positive";
    QString invalid = "Invalid";


    if (vibe.open(QIODevice::ReadWrite)){
        //vibe.setDataTerminalReady(true);
        // Port opened successfully
        QString v = "Connection to Vibe Successful!";
        qDebug() << v;

        QString patientName = "";

        // Names to map to barcode data
        QStringList names = { "Jill Scott", "Tom Hanks","Joe Rogan",
             "Kevin Hart", "Will Smith" };
ui->resultsField->setText("Invalid");
        // Barcode data to map to names
        QStringList barcodes = {"#11111111\r", "#22222222\r", "#33333333\r",
            "#44444444\r", "#55555555\r" };

        QByteArray sendVData = "#TRGON\r";
        //QByteArray sendData = "#REVSOFT\r";

        vibe.write(sendVData);
        //vibe.flush();
        qDebug() << "Data sent to vibe " + sendVData;
        //vibe.seek(0);

        vibe.waitForReadyRead();
        qDebug() << vibe.errorString();
        //vibe.waitForReadyRead(5000);
        QByteArray vData = vibe.readAll();

        qDebug() << "Data in Vibe: " << vData;






        bool isValid = false;
        for (int i = 0; i < barcodes.length(); i++)
        {
            for (int pos = 0; pos < barcodes.length(); pos++)
            {
                //If verified, set name to patient name
                qDebug() << "Current value of i: " + barcodes[i];
                if (vData == barcodes[i])
                {
                    patientName = names[i];
                    isValid = true;
                }
            }

        }
        if(isValid == false)
            patientName = "Invalid...";
        ui->patientField->setText(patientName);
        vibe.close();


    }
    else {
        // Handle the case when the port fails to open
        qDebug() << "Error Connectin to Vibe....";
    }
ui->resultsField->setText("Invalid");
    if (pW.open(QIODevice::ReadWrite)){
        pW.clear(QSerialPort::AllDirections);
        QByteArray sendPData = "#TEST\r";
        pW.write(sendPData);
        pW.waitForBytesWritten(1000);
        qDebug() << "Data sent to PennyWhistle " + sendPData;
        pW.waitForReadyRead(4000);
        QByteArray pData = pW.readAll();

        qDebug() << "Length of pData " << QString(pData).size();
        QByteArray finalData = "";
        bool check = false;
        while(check == false) {
            pW.clear(QSerialPort::AllDirections);
            pW.write(sendPData);
            pW.waitForBytesWritten(2000);
            qDebug() << "Data sent to PennyWhistle " + sendPData;
            pW.waitForReadyRead(4000);
            QByteArray pData = pW.readAll();
            qDebug() << "Data read from PennyWhistle " << pData;
            if (QString(pData).size() < 40){
                if (pData.contains("Pos") || pData.contains("Neg") ||
                    pData.contains("Inv")){
                    finalData = pData;
                    check = true;
                }
                usleep(200);
            }


        }

        if(finalData.contains("Invalid")){
            ui->resultsField->setStyleSheet("backgorund-color: white; color: orange;");
            ui->resultsField->setText("Invalid");


            qDebug() << "" << pData;
        }
        if(finalData.contains("Positive")){
            ui->resultsField->setStyleSheet("backgorund-color: white; color: red;");
            ui->resultsField->setText("Positive");
            qDebug() << "" << pData;
        }
        if(finalData.contains("Negative")){
            ui->resultsField->setStyleSheet("backgorund-color: white; color: green;");
            ui->resultsField->setText("Negative");
            qDebug() << "" << pData;
        }

        qDebug() << "Data in PennyWhistle: " << finalData;
        pW.clear(QSerialPort::AllDirections);
        pW.close();
    }
    else {
        // Handle the case when the port fails to open
        qDebug() << "Error Connectin to PennyWhistle....";
    }
}




void MainWindow::on_read_released()
{
    TMR_Reader r, * rp = NULL;
    TMR_Status ret;
    TMR_ReadPlan plan;
    TMR_ReadListenerBlock rlb;
    TMR_ReadExceptionListenerBlock reb;
    uint8_t antennaList[] = { 1 };

    rp = &r;

    ret = TMR_create(rp, "tmr:///dev/ttyUSB0");
    std::cout << __LINE__ << "Creating!\n";
    ret = TMR_connect(rp);
    std::cout << __LINE__ <<  "Connecting!\n";

    //needed to read more than once
    bool readFilter = false;
      ret = TMR_paramSet(rp, TMR_PARAM_TAGREADDATA_ENABLEREADFILTER, &readFilter);


    ret = TMR_RP_init_simple(&plan, 1, antennaList, TMR_TAG_PROTOCOL_ISO14443A, 1000);
    std::cout << __LINE__ <<  "Read Plan!\n";
    ret = TMR_paramSet(rp, TMR_PARAM_READ_PLAN, &plan);
    std::cout << __LINE__ <<  "Param Set!\n";
    rlb.listener = callback;
    rlb.cookie = NULL;

    reb.listener = exceptionCallback;
    reb.cookie = NULL;

    ret = TMR_addReadListener(rp, &rlb);
    checkerr(rp, ret, 1, "adding read listener");
    std::cout << __LINE__ <<  "Connecting\n";
    ret = TMR_addReadExceptionListener(rp, &reb);
    std::cout << __LINE__ <<  "Connecting!\n";
    ret = TMR_startReading(rp);
    std::cout << __LINE__ <<  "Connecting!\n";
        while(test == ""){
        //block access to the analyse button
          std::cout << __LINE__ <<  "While!\n";
          //usleep(100000);
          std::cout << test.toStdString();
        }
        if(test == "76B2"){
            test = "G.McIntyre";
            ui->analyse->setDisabled(false);
        }
        else if(test == "56D6"){
            test = "S.Dixon";
            ui->analyse->setDisabled(false);
        }
        else{
            test = "Invalid User...";
            ui->analyse->setDisabled(true);
        }
        ui->physicianField->setText(test);
        test = "";

    ret = TMR_stopReading(rp);
    checkerr(rp, ret, 1, "stopping reading");
    //ret = TMR_flush(rp);
    ret = TMR_destroy(rp);
    std::cout << __LINE__ <<  "Reader Disconnected!\n";
}

void MainWindow::on_read_pressed()
{
    test = "";
    ui->analyse->setDisabled(true);
    ui->physicianField->clear();

}
