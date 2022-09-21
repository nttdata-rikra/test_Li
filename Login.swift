import Alamofire
import Network

// ログイン処理
func login(userId: String, password: String) -> (result: Bool, messageId: String) {
    // 送信処理
    let url = Consts.URL_BASE + "login/login/ward-native/"
    let parameters = [
        "user_id": userId,
        "password": password
    ]
    
    func sendData() -> (result: Bool, messageId: String) {
        var result = false
        var messageId = ""
        AF.request(url, method: .post, parameters: parameters, requestModifier: { $0.timeoutInterval = 5.0 }).validate().response { (response) in
            switch response.result {
            case .success:
                var checkResult = false
                if let unwrapped = response.data {
                    do {
                        let json = try JSONSerialization.jsonObject(with: unwrapped)
                        let d = json as! [String: Any]
                        guard let checkResultTmp = d["result"] as? Bool else {return}
                        checkResult = checkResultTmp
                    } catch {
                    }
                }
                if(checkResult == false) {  // 認証が通らなかった場合
                    (result, messageId) = (false, "error.SC_A10_01.00001")
                } else {  // 認証が通った場合
                    (result, messageId) =  (true, "")
                }
                
                
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
