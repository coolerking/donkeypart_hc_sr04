#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超音波距離センサモジュール HC-SR04（SparkFun販売品）
https://www.switch-science.com/catalog/2860/

- 仕様
 - 電源電圧: 5 V
 - 待機電流: 2 mA未満
 - 信号出力: 0～5 V
 - センサ角度: 15 度以下
 - 測定可能距離: 2～400 cm
    分解能: 0.3 cm
    端子間隔: 2.54 mm

- 使い方
 - トリガ端子を10 us以上Highにしてください。
 - このセンサモジュールが40 kHzのパルスを8回送信して受信します。
 - 受信すると、出力端子がHighになります。
 - 出力端子がHighになっている時間がパルスを送信してから受信するまでの時間です。
 - 出力端子がHighになっている時間の半分を音速で割った数値が距離です。

"""
import time

import pigpio

LONGEST_TIME = 20000

class Driver:
    """
    このクラスは一種の音響距離計測器をカプセル化します。
    特に別々のトリガーとエコーピンを持つ距離計測のタイプをさします。

    トリガーのパルスがソナーのpingを開始し、
    その直後にソナーのパルスが送信され、
    エコーピンがハイになります。
    エコーピンは、ソナーエコーが受信されるまで
    （または応答がタイムアウトするまで）ハイのままです。
    ハイエッジとローエッジの間の時間は、ソナーの往復時間を示します。
    """

    def __init__(self, pi, trigger, echo):
        """
        使用するPiオブジェクト、トリガGPIO番号およびエコーGPIO番号を受け取ります。
        引数
            pi          gpio.piオブジェクト
            trigger     Trigピンが接続されているGPIO番号
            echo        Echoピンが接続されているGPIO番号
        戻り値
            なし
        """
        # インスタンス変数初期化
        self.pi    = pi
        self._trig = trigger
        self._echo = echo

        # ソナーがping中であるかどうか
        self._ping = False
        # Echoピンがハイになった時刻（マイクロ秒）
        self._high = None
        # Echoピンがハイになっていた時刻
        self._time = None

        # トリガされているかどうか
        self._triggered = False

        # 開始前の各GPIOの状態を保管
        self._trig_mode = pi.get_mode(self._trig)
        self._echo_mode = pi.get_mode(self._echo)

        # GPIO初期化
        pi.set_mode(self._trig, pigpio.OUTPUT)
        pi.set_mode(self._echo, pigpio.INPUT)

        # Trigピンにコールバック関数をセット
        self._cb = pi.callback(self._trig, pigpio.EITHER_EDGE, self._cbf)
        # Echoピンにコールバック関数をセット
        self._cb = pi.callback(self._echo, pigpio.EITHER_EDGE, self._cbf)

        # 初期化したかどうか
        self._inited = True

    def _cbf(self, gpio, level, tick):
        """
        コールバック関数
        引数
            gpio   0〜31   状態が変化したGPIO番号
            level   0〜2    0 =ローに変化（立ち下がりエッジ）
                            1 =ハイに変化（立ち上がりエッジ）
                            2 =レベル変更なし（ウォッチドッグタイムアウト）
            tick    32bit   起動後のマイクロ秒数
                            警告：これはおよそ72分ごとに4294967295から0に折り返される
        """
        # Trigピンの場合
        if gpio == self._trig:
            # トリガPinがハイ＝トリガ送信済みの場合
            if level == 0:
                # 送信済み状態にする
                self._triggered = True
                # Echoピンがハイになった現在時刻を削除
                self._high = None
        # Echo ピンの場合
        else:
            # トリガ送信済みの場合
            if self._triggered:
                # Echoピンがハイになった場合
                if level == 1:
                    # Echoピンがハイになった現在時刻（マイクロ秒）を保管
                    self._high = tick
                # Echoピン変化なしもしくはローになったとき
                else:
                    # 現在時刻が保管されている場合
                    if self._high is not None:
                        # Echoピンがハイになっていた時間（マイクロ秒）を計算
                        self._time = tick - self._high
                        # Echoピンがハイになった現在時刻を削除
                        self._high = None
                        # Echoピンによる時間計測した状態にする
                        self._ping = True

    def read(self):
        """
        読み取りを開始する。 
        返される読み取り値は、ソナーの往復のマイクロ秒数となる。
        往復cms =往復時間/ 1000000.0 * 34030
        引数
            なし
        戻り値
            distance    cm  距離
                            Noneの場合はタイムアウトもしくは計測不能
        """
        # 初期化済みの場合
        if self._inited:
            # Echoピンによる時間計測していない状態にする
            self._ping = False
            # Trigピンにトリガ信号を送信
            self.pi.gpio_trigger(self._trig, 11, pigpio.HIGH)
            # Trigピンにトリガ信号を送信した時刻を保管
            start = time.time()
            # Echoピンによる時間計測が終わるまでループ
            while not self._ping:
                # 5秒以上待機した場合
                if (time.time()-start) > 5.0:
                    return duration_to_distance(LONGEST_TIME)
                # 1ミリ秒待機
                time.sleep(0.001)
            # Echoピンがハイになっていた時間を返却
            return duration_to_distance(self._time)
        else:
            return None

    def cancel(self):
        """
        距離計測をキャンセルしてgpiosを元のモードに戻す。
        引数
            なし
        戻り値
            なし
        """
        if self._inited:
            # 初期化前の状態にする
            self._inited = False
            # コールバック関数の解除
            self._cb.cancel()
            # 初期化前に保管していた状態に戻す
            self.pi.set_mode(self._trig, self._trig_mode)
            self.pi.set_mode(self._echo, self._echo_mode)

def duration_to_distance(duration):
    """
    Echoピンがハイになっていた時間を距離に変換する。
    引数
        duration    Echoピンがハイになっていた時間 (マイクロ秒)
    戻り値
        distance    距離 (cm)
                    Noneの場合はタイムアウトもしくは計測不能
    """
    if duration is None or duration < 0 or duration == LONGEST_TIME:
        return None
    else:
        # 往復距離なので2で割り、音速で割って距離化(cm)
        return (duration / 2.0) * 340.0 * 100.0 / 1000000.0

if __name__ == "__main__":
    import time
    import pigpio
    RANGE_TRIG_GPIO = 5
    RANGE_ECHO_GPIO = 6
    RANGE_GPIOS = [
        RANGE_TRIG_GPIO,
        RANGE_ECHO_GPIO
    ]
    pi = pigpio.pi()
    sonar = Driver(pi, RANGE_GPIOS[0], RANGE_GPIOS[1])

    end = time.time() + 600.0

    r = 1
    while time.time() < end:

        print("{} {}".format(r, sonar.read()))
        r += 1
        time.sleep(0.03)

    sonar.cancel()

    pi.stop()
