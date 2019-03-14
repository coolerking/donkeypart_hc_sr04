# Donkey Carに超音波距離計測センサを搭載する

## HC-SR04

ここでは、[超音波距離センサモジュール HC-SR04（SparkFun販売品）](https://www.switch-science.com/catalog/2860/) を使用します。

### 製品諸元

| 項目名 | 値 |
|:-----|--:|
| 電源電圧 | 5 V |
| 待機電流 | 2 mA未満 |
| 信号出力 | 0～5 V |
| センサ角度 | 15 度以下 |
| 測定可能距離 | 2～400 cm |
| 分解能 | 0.3 cm |
| 端子間隔 | 2.54 mm |

### ピン仕様

ピン仕様は、以下の図のとおりです。

![HC-SR04のピン配置](./assets/hc-sr04.png)

### 計測方法

1. トリガ端子を10 us以上Highにしてください。
2. このセンサモジュールが40 kHzのパルスを8回送信して受信します。
3. 受信すると、出力端子がHighになります。
4. 出力端子がHighになっている時間がパルスを送信してから受信するまでの時間です。
5. 出力端子がHighになっている時間の半分を音速で割った数値が距離です。

## パーツクラスのインストール

### センサの接続

Raspberry Pi を停止状態にして、以下の図の接続例のようにセンサを結線します。

![回路図](./assets/circuit.png)

|センサ側|Raspberry Pi側|備考|
|:------|:-------------|:---|
|Vcc|5V|5Vで稼働する|
|Trig|GPIO5|何も割り当てられていないGPIOピンでよい|
|Echo|GPIO6|何も割り当てられていないGPIOピンでよい|
|Gnd|GND|GNDのいずれか１つのピンでよい|


### pigpioパッケージのインストール

1. Raspberry Piを起動し、SSH接続する
2. `sudo apt install -y pigpio` を実行する
3. `cd ~/`
4. `git clone http://pandagit.exa-corp.co.jp/git/89004/donkeypart_sonicrangesensor.git` を実行する
5. `cd donkeypart_sonicrangesensor`
6. `pip install -e .` を実行する

### config.pyの編集

1. 接続したGPIOピン番号をもとに`config.py`を編集する
   ```python
   RANGE_TRIG_GPIO = 5
   RANGE_ECHO_GPIO = 6
   RANGE_GPIOS = [
       RANGE_TRIG_GPIO,
       RANGE_ECHO_GPIO
   ]
   ```

### manage.pyの編集
1. manage.pyの関数driveの適当な位置にパーツ`Sensor`を追加する
   ```python
       :
       import pigpio
       pi = pigpio.pi()
       :

       :
       from donkeypart_sonicrangesensor import Sensor
       range = Sensor(pi, cfg.RANGE_GPIOS)
       V.add(range, outputs=['range/cms'], threaded=True)
       :
   ```

> Tubデータとして使用する場合は、TubWriterの設定を変更してください。

## ライセンス

本リポジトリのソースコードは [MITライセンス](./LISENSE) 準拠とします。