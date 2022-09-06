import Alamofire
import Network
// ログイン処理
func login(userId, password) {
    // 送信処理
    let url = "/login/ward-native"
    let paramaters = [
        "user_id":userId,
        "password":password
    ]
    Alamofire.request(url,method: .post,paramaters:paramaters).responseJSON {
        response in
        switch response.result {
        case .success(let data):
            if data.result { // 認証が通った場合  
                return (true, "");
            } else { // 認証が通らなかった場合
                return (false, "error.SC_A10_01.00001");
            }
        case .failure():
            if textStatus ==  Consts.LOGIN_TIMEOUT_TIME { // タイムアウトが発生した場合
                return (false, "error.common.timeout");
            } else { // その他システムエラーの場合
                return (false, "error.common.system_error");
            }
        }
    })
}

//ネットワークチェック
monitor.pathUpdateHandler = { path in
        if path.status == .satisfied {
            login()
        }else{
            //ダイアログ表示(error.common.network)
        }
    }
monitor.start(queue:queue)
