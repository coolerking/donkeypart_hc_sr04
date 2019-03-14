# -*- coding: utf-8 -*-
"""
Donkey Car に搭載可能な距離計測センサをあらわすパーツクラス。
"""
import pigpio
import time

# Vehicleループがデフォルト(20 MHz)の場合距離計測が2回実行される
WAIT_TIME = 0.025

class Sensor:
    """
    Donkey Carに接続された距離計測センサをあらわすパーツクラス。
    """
    def __init__(self, pi, range_gpios):
        '''
        フォークリフトに搭載された超音波センサ用ドライバを初期化する。

        引数：
            pi          pigpioパッケージのpiオブジェクト
            pu_gpios    パワーユニット用GPIO番号が格納された２次元配列
        '''
        self.pi = pi
        if range_gpios is not None:
            from .hc_sr04 import Driver
            self.range = Driver(self.pi, range_gpios[0], range_gpios[1])
        else:
            self.range = None
        self.distance = None

    def update_loop_body(self):
        """
        update()内で実行されるループ本体処理をきりだしたもの。
        ソナーを打ち、計測した距離を取得、インスタンス変数distanceへ格納する。
        その後、一定時間待機。

        引数
            なし
        戻り値
            なし
        """
        self.distance = self.range.read()
        time.sleep(WAIT_TIME)

    def update(self):
        """
        別スレッドで実行される処理を実装する。
        ドライバクラスを呼び出し定期的にインスタンス変数distanceへ計測結果を
        格納する処理を実装する。

        引数
            なし
        戻り値
            なし
        """
        if self.range is not None:
            while True:
                self.update_loop_body()
        else:
            return None
    
    def run_threaded(self):
        """
        別スレッドで常に最新計測結果が格納されているインスタンス変数distanceを
        返却する。

        引数
            なし
        戻り値
            distance    計測結果距離(cm)
        """
        return self.distance
    
    def run(self):
        if self.range is not None:
            self.distance = self.range.read()
        return self.distance
    
    def shutdown(self):
        """
        シャットダウン時処理を実装する。
        ドライバにGPIO設定を起動前状態に戻す処理を実行させる。

        引数
            なし
        戻り値
            なし
        """
        if self.range is not None:
            self.range.cancel()
            self.range = None
            self.distance = None
