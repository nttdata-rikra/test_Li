import Alamofire
import Network

func getPatientList() -> (result: Bool, messageId: String, patientInformation: [[String: Any]]) {
    let urlString = Consts.URL_BASE + "ward/patient_select/get_patient"
    
    func getData() -> (result: Bool, messageId: String, patientInformation: [[String: Any]]) {
        var patientInformation: [[String: Any]] = [["": ""]]
        var result = false
        var messageId = ""
        AF.request(urlString, method: .post, requestModifier: {$0.timeoutInterval = 5.0}).validate().response { (response) in
            switch response.result {
            case .success:
                if let unwrapped = response.data {
                    do{
                        let json = try JSONSerialization.jsonObject(with: unwrapped)
                        let d = json as! [String: String]
                        if d.keys.contains("result") {
                            let sessionCheckResult = d["result"]
                            if(sessionCheckResult == "NG") {  //セッションチェックエラー時
                                (result, messageId) = (false, "warn.common.session")
                            }
                        }else{
                            if let infos = d["data"]?.data(using: .utf8) {
                                let pinfo  = try JSONSerialization.jsonObject(with: infos) as! [[String: Any]]
                                (result, messageId, patientInformation) = (true, "", pinfo)
                            }
                        }
                    }catch {
                    }
                }
                
            case .failure(let error):
                //タイムアウトが発生した場合
                if error.isSessionTaskError {
                    (result, messageId, patientInformation) =  (false, "error.common.timeout", [["": ""]])
                    //その他システムエラーの場合
                }else{
                    (result, messageId, patientInformation) =  (false, "error.common.system_error", [["": ""]])
                }
            }
        }
        return (result, messageId, patientInformation)
    }
        
        
    //ネットワークチェック
   if Network.shared.isOnline() {
       return getData()
   } else {
       return (false, "warn.common.network", [["": ""]])
   }
}
