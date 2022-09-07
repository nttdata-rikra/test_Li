if error._code == NSURLErrorTimedOut
に対応するのは、以下のリンク先の行。if(textStatus == Consts.RECORDING_SEND_TIMEOUT_TIME){
の行。なので、{}の中にはいるのは retryCount++と、上のリトライのやつ。

で、タイムアウトという仕組みを実現するには、「リクエストからn秒たったらタイムアウトね！」というのを教えてやらなきゃいけなくて、
そのためには、
, requestModifier: { $0.timeoutInterval = 5.0 })
を入れる必要がある。（5.0のところは、動作確認終わった後で定数に置き換えましょう）

  Thread.sleep(forTimeInterval: Consts.RECORDING_SEND_RETRY_WAIT_TIME - Consts.RECORDING_SEND_TIMEOUT_TIME)

sendData()

の2行を入れれば行ける、はず。ただし、確証がないので、

Thread.sleep(forTimeInterval: Consts.RECORDING_SEND_RETRY_WAIT_TIME - Consts.RECORDING_SEND_TIMEOUT_TIME)

s

はコメントにしといて、仮置きで

Thread.sleep(forTimeInterval: 5)

と書いておいてほしい
