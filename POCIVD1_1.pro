QT       += core gui
QT       += serialport
CONFIG += console
greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++11

# The following define makes your compiler emit warnings if you use
# any Qt feature that has been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    hex_bytes.c \
    main.cpp \
    mainwindow.cpp \
    osdep_posix.c \
    serial_reader.c \
    serial_reader_l3.c \
    serial_transport_posix.c \
    tm_reader.c \
    tm_reader_async.c \
    tmr_loadsave_configuration.c \
    tmr_param.c \
    tmr_strerror.c \
    tmr_utils.c

HEADERS += \
    mainwindow.h \
    osdep.h \
    serial_reader_imp.h \
    tm_config.h \
    tm_reader.h \
    tmr_filter.h \
    tmr_gen2.h \
    tmr_gpio.h \
    tmr_ipx.h \
    tmr_iso14443a.h \
    tmr_iso14443b.h \
    tmr_iso15693.h \
    tmr_iso180006b.h \
    tmr_lf125khz.h \
    tmr_lf134khz.h \
    tmr_llrp_reader.h \
    tmr_params.h \
    tmr_read_plan.h \
    tmr_region.h \
    tmr_serial_reader.h \
    tmr_serial_transport.h \
    tmr_status.h \
    tmr_tag_auth.h \
    tmr_tag_data.h \
    tmr_tag_lock_action.h \
    tmr_tag_protocol.h \
    tmr_tagop.h \
    tmr_types.h \
    tmr_utils.h

FORMS += \
    mainwindow.ui

# Default rules for deployment.
# qnx: target.path = /tmp/$${TARGET}/bin
# else: unix:!android: target.path = /data/bin/$${TARGET}
target.path = /data/bin/$${TARGET}
!isEmpty(target.path): INSTALLS += target

DISTFILES += \
    Doxyfile \
    mercuryapi.cfg \
    samples.mk
