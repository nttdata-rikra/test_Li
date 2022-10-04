import socket

# 指定バイト数分文字列切り出し
def slice_with_byte(message, start, byte_num):
  return message.encode('sjis')[start:start+byte_num].decode('sjis')

host1 = '127.0.0.1' # 要カスタマイズ
port1 = 2021 # 要カスタマイズ

patient_informations = {
    "1         " : ["テストヨウカンジャ０１", "試験用患者０１", "1", "19500101"],
    "2         " : ["テストヨウカンジャ０２", "試験用患者０２", "2", "19500201"],
    "3         " : ["テストヨウカンジャ０３", "試験用患者０３", "1", "19500301"],
    "4         " : ["テストヨウカンジャ０４", "試験用患者０４", "2", "19500401"],
    "5         " : ["テストヨウカンジャ０５", "試験用患者０５", "1", "19500501"],
    "6         " : ["テストヨウカンジャ０６", "試験用患者０６", "2", "19500601"],
    "7         " : ["テストヨウカンジャ０７", "試験用患者０７", "1", "19500701"],
    "8         " : ["テストヨウカンジャ０８", "試験用患者０８", "2", "19500801"],
    "9         " : ["テストヨウカンジャ０９", "試験用患者０９", "1", "19500901"],
    "10        " : ["テストヨウカンジャ１０", "試験用患者１０", "2", "19501001"],
    "11        " : ["テストヨウカンジャ１１", "試験用患者１１", "1", "19501101"],
    "12        " : ["テストヨウカンジャ１２", "試験用患者１２", "2", "19501201"],
    "13        " : ["テストヨウカンジャ１３", "試験用患者１３", "1", "19510101"],
    "14        " : ["テストヨウカンジャ１４", "試験用患者１４", "2", "19510201"],
    "15        " : ["テストヨウカンジャ１５", "試験用患者１５", "1", "19510301"],
}

socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket1.bind((host1, port1))
socket1.listen(1)
print("リクエスト受付開始")
while True:
    connection, address = socket1.accept()
    req = connection.recv(4096).decode()
    patient_id = slice_with_byte(req, 65, 10)
    print("リクエストを受信　患者ID=", patient_id, "")
    # 以下、応答電文です
    # 患者IDについては、依頼電文から抽出して埋め込みます
    # 名前・性別・生年月日部分は適宜修正願います
    answer = "                                         OK                        " + patient_id + patient_informations[patient_id][0] + "                                      " + patient_informations[patient_id][1] + "                " + patient_informations[patient_id][2] + patient_informations[patient_id][3] + "                                                                                                                                                                                    "
    connection.send(answer.encode("sjis"))
    
    connection.close()

socket1.close()
