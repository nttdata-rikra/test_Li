import Alamofire
import Network

// ログアウト処理
func logout()-> (result: Bool, messageId: String) {
    // 送信処理
    let url = Consts.URL_BASE + "login/logout/ward-native/"
    
    func sendData() -> (result: Bool, messageId: String) {
        var result = false
        var messageId = ""
        AF.request(url, method: .post, requestModifier: { $0.timeoutInterval = 5.0 }).validate().response {(response) in
            switch response.result {
            case .success:
                (result, messageId) =  (true, "")
                
                
            case .failure(let error):
                //タイムアウトが発生した場合
                if error.isSessionTaskError {
                    (result, messageId) =  (false, "error.common.timeout")
                //その他システムエラーの場合
                } else {
                    (result, messageId) =  (false, "error.common.system_error")
                }
            }
        }
        return (result, messageId)
    }
    
    //ネットワークチェック
   if Network.shared.isOnline() {
        return sendData()
   } else {
       return (false, "warn.common.network")
   }
}
