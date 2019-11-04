<?php
error_reporting(E_ALL);
//header('Content-Type: application/json');
ini_set('display_errors', 1);
require "suFunctions.php";

$GLOBALS['LOG_LEVELS'] = ['error','warn','info','debug'];
$GLOBALS['LOG_LEVEL'] = "info";
$GLOBALS['SEND_LIMIT'] = 3;
$GLOBALS['SEND_AMOUNT'] = 10;
$GLOBALS['SEND_WAIT_LIMIT'] = 1;

date_default_timezone_set('Europe/Istanbul');

//istekler POST olarak gönderilmeli, Bip oyle yapiyor.
if (strcasecmp($_SERVER['REQUEST_METHOD'], 'POST') != 0) {throw new Exception('Request method must be POST!');}

//Make sure that the content type of the POST request has been set to application/json
$contentType = isset($_SERVER["CONTENT_TYPE"]) ? trim($_SERVER["CONTENT_TYPE"]) : '';

if (strcasecmp($contentType, 'application/json') != 0) {throw new Exception('Content type must be: application/json');}

//Receive the RAW post data.
$contentFromBip = trim(file_get_contents("php://input"));

//Attempt to decode the incoming RAW post data from JSON.
$decoded = json_decode($contentFromBip, true);

logr("main","debug","1request: ".$contentFromBip);

clean_buffer();
header("Connection: close\r\n");
header("Content-Encoding: none\r\n");
ignore_user_abort(true); // optional
ob_start();
echo ('Request received. Will be processed soon.');
$size = ob_get_length();
header("Content-Length: $size");
ob_end_flush(); // Strange behaviour, will not work
flush(); // Unless both are called !
clean_buffer();


//bip'ten gelen json mesajı çözümleyelim
foreach ($decoded as $key => $val) {
    //print "$key = $val\n";

    if ($key == "content") {
        $keyword = $val;
    }

    if ($key == "msgid") {
        $msgId = $val;
    }

    if ($key == "sender") {
        $sender = $val;
    }

    if ($key == "sendtime") {
        $sendtime = $val;
    }

    if ($key == "postback") {
        $postback = $val;
    }

    if ($key == "ctype") {
        $ctype = $val;
    }

    if ($key == "poll") {
        $poll = $val;
    }
}

//quick menu cevabı
if (isset($postback)) {
    foreach ($postback as $key => $val) {
        if ($key == "payload") {
            $payload = $val;
            $payloadMessage = strtolower($payload);
        }
        if ($key == "postbackid") {
            $postbackID = $val;
            //$postbackID=strtolower($postbackID);
        }

    }
}

//anket cevabi
if (isset($poll)) {
    foreach ($poll as $key => $val) {
        if ($key == "optionids") {
            $optionids = $val;
            $optionPoll = $optionids[0];
        }
        if ($key == "pollid") {
            $pollIDFull = explode("-",$val);
            $pollID = $pollIDFull[0];
            $pollIDExt = sizeof($pollIDFull) > 1 ? $pollIDFull[1] : "";
        }
    }
}

//fastcgi_finish_request();

//gelen mesajın içerisini ekrana basalim
//echo "\nkeyword is: ".$keyword;
//echo "\nmsgId is: ".$msgId;
//echo "\nsender is: ".$sender;
//echo "\nsendtime id is: ".$sendtime;

$bul = array('ç', 'ğ', 'ş', 'ö', 'ü', 'ı');
$degistir = array('c', 'g', 's', 'o', 'u', 'i');
$keyword = str_replace($bul, $degistir, isset($keyword) == true ? $keyword : "");

$wordCount = str_word_count($keyword);
//echo "\nkeyword word count: ".$wordCount;
//echo "\nkeywordLT: ".$keywordLT;
//echo "\nkeywordRT: ".$keywordRT;
//echo "\napp control result 0/1: ".$appControl;
//$appCresult=" CR: ";
//if ($appControl=0) {$appCresult="istek servis ismi icermiyor";}
//echo "\nAppcontrol array printR: ";
//print_r($appControl)." ".$appCresult;

//print_r($applist);
//echo "\napplist: ";
//print_r($applist);
$receiver = $sender;
$msisdn = substr($sender, 2, 10);
$userID = getuserIDByMSISDN($msisdn);
$publicWalletID = getWalletID($userID);
$timestamp = time();

//If json_decode failed, the JSON is invalid.
if (!is_array($decoded)) {
    throw new Exception('Received content contained invalid JSON!');
}

//$keyword=strtolower($keyword);
$keywords = explode(" ", $keyword);
$maxWordC = sizeof($keywords);
$keywordLT = strtolower($keywords[0]);
$keywordRT = $maxWordC>1 ? $keywords[1] : null;
$keywordP3 = $maxWordC>2 ? $keywords[2] : null;

for ($i = 3; $i < $maxWordC; $i++) {
    $keywordMessage = $keywordMessage . " " . $keywords[$i];
}
//$keywordMessageEncoded=base64_encode('no_message');
if (!isset($keywordMessage)) {$keywordMessage = 'jet gonderi';}
$keywordMessageEncoded = base64_encode($keywordMessage);

$komutlar = array('yolla', 'puan', 'yardim', 'liste', 'sifre', 'menu', '', '', 'pot15', 'hgx1', 'anket', 'jet', 'top5ms', 'son5giden', 'son5gelen','topres','tranco');
$commandControl = in_array($keywordLT, $komutlar);

if ($commandControl == 0) {
    $hasTransaction = hasWaitingTransaction($publicWalletID,$GLOBALS['SEND_WAIT_LIMIT']);
    if($hasTransaction == false){
        $bakiye = getIMSBalance($publicWalletID);
        if($bakiye >= $GLOBALS['SEND_AMOUNT']){
            //$content="Hatalı istek yaptın. Yardım yazarak sihirli kelimelere erişebilirsin.";
            $tnxid = rand(1000, 20000);
            //$content=sendReceiverPollFromDB($receiver);
            $tribeID = getTribeID($userID);
            $myList = getPollReceiverlistShort($keyword, $tribeID);
            $myListCount = getPollReceiverlistCount($keyword, $tribeID);
            //$content='$myListCount: '.$myListCount.' \n $myList: '.$myList;
            if ($myList == '') {
                $content = strtoupper($keyword) . " ile başlayan alıcı ismi bulamadım. \n\n👋🏻Telefonunu sallayarak hızlı menüye ulaşabilirsin.\n\nYardım yazarak sihirli kelimelere ulaşabilirsin. ";
            } else if ($myListCount == 1) {
                $anket = '{
                    "txnid":"' . $tnxid . '",
                    "receiver":{
                        "type":2,
                        "address": "' . $receiver . '"
                    },
                    "composition":{
                        "list":[
                        {
                            "type":13,
                            "tmmtype":2,
                            "polltmm":{
                                "title":"' . strtoupper($keywordLT) . ' ile başlayan alıcı isimleri aşağıda.",
                                "description":"İsmi seçip '.$GLOBALS['SEND_AMOUNT'].' IMS Yolla! \n\n👋🏻Diğer işlemler için telefonu salla menü gelsin. ",
                                "polltype":0,
                                "pollid":"hizlianket",
                                "image":{
                                    "url":"http://timsac.turkcell.com.tr/scontent/p2p/19022018/09/Pe336b30c03db3493052cdede73334c1b57443c13c219e3b7d70441d99add1e0d7.png",
                                    "ratio":1
                                },
                                "optionlist":[
                                {
                                    "optionid":' . $userID . ',
                                    "name":"' . getReceiverNamebyUserID($userID) . '"
                                    }' . $myList . '
                                ],
                                "buttonname":"Yolla"
                            }
                        }
                        ]
                    }
                }';
                
            } else {
                $myList = getPollReceiverlistLong($keywordLT, $tribeID);
                $anket = '{
                    "txnid":"' . $tnxid . '",
                    "receiver":{
                        "type":2,
                        "address": "' . $receiver . '"
                    },
                    "composition":{
                        "list":[
                        {
                            "type":13,
                            "tmmtype":2,
                            "polltmm":{
                                "title":"' . strtoupper($keywordLT) . ' ile başlayan alıcı isimleri aşağıda.",
                                "description":"İsmi seçip '.$GLOBALS['SEND_AMOUNT'].' IMS Yolla! \n\n👋🏻Diğer işlemler için telefonu salla menü gelsin. ",
                                "polltype":0,
                                "pollid":"hizlianket",
                                "image":{
                                    "url":"http://timsac.turkcell.com.tr/scontent/p2p/19022018/09/Pe336b30c03db3493052cdede73334c1b57443c13c219e3b7d70441d99add1e0d7.png",
                                    "ratio":1
                                },
                                "optionlist":[
                                ' . $myList . '
                                ],
                                "buttonname":"Yolla"
                            }
                        }
                        ]
                    }
                }';
                
            }
                
            $result = sendBipResponseIncReceiver($anket);
        } else {
            sendBipResponseErza($receiver, "Maalesef bakiyen yetersiz. Biraz da teşekkür almaya bak ya da Pazartesiyi bekle :)");
        }
    } else {
        sendBipResponseErza($receiver, "Çok mu sık teşekkür ediyorsun acaba :) 1 dk beklemen gerekiyor maalesef.");
    }
}

//content baslangic

//if ($keywordLT=='' && $payloadMessage=='') {

if ($ctype == 'Buzz') {
//$senderName=getNamebyPhone($msisdn);
    //wellcome message olarak kullanılıt, titreşim yolladığında vs durumlarda da bu yanıt dönülür...
    //$content="Hoşgeldin ".$senderName."\n\nYardım yazarak HappyChain'de kullanabileceğin komutlara ulaşabilirsin.\n\n http://happychain.ga" ;
    $result = sendQuickMenu($receiver);
//$content=$result."-----".$ctype."log: ".$receiver;
}

if ($keywordLT == 'yardim' || (isset($payloadMessage) && $payloadMessage == 'yardim')) {
    $content = "Puan sorgulamak için PUAN yaz gönder. \n\nArkadaşına puan göndermek için arkadaşının isminin ilk 3-4 harfini yaz, gelen listeden seçimini yap, puanı gönder.\n\nArkadaşlarının isimlerini liste halinde görmek için LISTE  yaz gönder.";
}

if ($keywordLT == 'hgx1') {
    $content = "Hoşgeldin " . getReceiverNamebyUserID($userID) . "\n\n👋🏻Telefonunu sallayarak hızlı menüye ulaşabilirsin.\n\nYardım yazarak sihirli kelimelere ulaşabilirsin.";
}

if ($keywordLT == 'puan' || (isset($payloadMessage) && $payloadMessage == 'puan') || (isset($optionPoll) && $optionPoll == 800)) {
    $bakiye = getIMSBalance($publicWalletID);
    $totalSent = getTotalSentIsActive($publicWalletID);
    $totalReceived = getTotalReceivedIsActive($userID);
    $content = "IMS Bakiyen: " . $bakiye . " IMS\n\nGönderdiğin: 👼 " . $totalSent . " IMS \nSana Gelen: 🙏 " . $totalReceived . " IMS";
}

if ($keywordLT == 'ekle') {
    $receiverAlias = $keywordRT;
    $receiverUserID = getuserIDbyAlias($receiverAlias);
    $result = createShortcut($userID, $receiverUserID);
    $content = $receiverAlias . ' hızlı gönder listene eklendi.';
}

if ($keywordLT == 'nasil' || (isset($payloadMessage) && $payloadMessage == 'nasil')) {
//$receiverList=getReceiverList();
    $content = "Teşekkür etmek istediğin biri mi var? O zaman pamuk eller cebe🤗\n
IMS transfer etmek için teşekkür etmek istediğin kişinin ilk birkaç harfini yaz ve gönder.
\nÖr: ETEL ERGÜN’e IMS göndermek istiyorsan “ete” yaz, yolla gelsin. 👍
\nGelen listeden arkadaşının adını bul ve yolla butonuna tıkla.
\nTeşekkür etmek için elbet bir sebebin vardır. Şimdi onu seçme zamanı. Gelen listeden teşekkür sebebini seç ve tekrar yolla butonuna tıkla.
\nTebrikler arkadaşına ".$GLOBALS['SEND_AMOUNT']." IMS yollamış oldun, tabi eğer yeterli bakiyen varsa🤗";
}

if ($ctype == 'Poll' && $pollID == 'hizlianket') {
    if ($optionPoll == 900) {
        $tribeID = getTribeID($userID);
        $randomReceiver = getRandomReceiver($tribeID, $userID);
        $optionPoll = $randomReceiver;
    }
    $receiverName = getReceiverNamebyUserID($optionPoll);
    $senderName = getNamebyPhone($msisdn);
	$receiverPhone = getPhonebyUserID($optionPoll);
	
	logr("Poll","debug","msisdn: ".$msisdn.", receiverPhone: ".$receiverPhone);
	if($receiverPhone == $msisdn){
		$msg = "Kendi kendine teşekkür etmen çok hoş ama arkadaşların da senden bir teşekkür bekliyor olabilir :)";
		sendBipResponseErza("90".$msisdn, $msg);
	}else{
		$receiverWalletID = getWalletID($optionPoll);
		$messageToSign = $receiverWalletID . $publicWalletID . $timestamp . '1000' . $GLOBALS['SEND_AMOUNT'] . '000';
		$messageBody = "\"sender\": \"" . $publicWalletID . "\",\"recipient\": \"" . $receiverWalletID . "\",
	  \"type1\": \"" . $GLOBALS['SEND_AMOUNT'] . "\",
	  \"type2\": \"0\",
	  \"type3\": \"0\",
	  \"type4\": \"0\",
	  \"amount\": \"0\",
	  \"sequence\":\"100\",
	  \"timestamp\":\"" . $timestamp . "\",
	  \"text\": \"" . $keywordMessageEncoded . "\"";

		$publicKey = getPublicKey($userID);
		$privateKey = getPrivateKey($userID);
		$signature = getSignature($publicKey, $privateKey, $messageToSign);
		$result = createTempFinRecord($msisdn, $signature, $messageBody, $receiverName, $receiverPhone);
		$optionList = getReasonOptions($optionPoll);

		$anket = '{
		 "txnid":"9999",
		 "receiver":{
			"type":2,
			"address": "' . $receiver . '"
		 },
		 "composition":{
			"list":[
			   {
				  "type":13,
				  "tmmtype":2,
				  "polltmm":{
					 "title":"' . getNameSuffix($receiverName) . ' teşekkür etmek istedin ve '.$GLOBALS['SEND_AMOUNT'].' IMS yolluyorsun.",
					 "description":"Arkadaşına hangi mesajı ileteyim? ",
					 "polltype":0,
					 "pollid":"reasonList",
					 "image":{
						"url":"http://timsac.turkcell.com.tr/scontent/p2p/15032018/11/Pc2de09311da2d8e88395bdacec4c53a40b8801012dc80f501c4f4e397e258b318.jpg",
						"ratio":1
					 },
					 "optionlist":'.$optionList.',
					 "buttonname":"Yolla"
				  }
			   }
			]
		 }
	  }';
	  
	  $result = sendBipResponseIncReceiver($anket);
	}

}

if ($ctype == 'Poll' && $pollID == 'hizlicevap') {
    if($optionPoll != 0){
        $hasTransaction = hasWaitingTransaction($publicWalletID,$GLOBALS['SEND_WAIT_LIMIT']);
        if($hasTransaction == false){
            $bakiye = getIMSBalance($publicWalletID);
            if($bakiye >= $GLOBALS['SEND_AMOUNT']){
                $receiverName = getReceiverNamebyUserID($optionPoll);
                $senderName = getNamebyPhone($msisdn);
                $receiverPhone = getPhonebyUserID($optionPoll);

                $receiverWalletID = getWalletID($optionPoll);
                $controlRLimit = GetReceiverLimit($publicWalletID, $receiverWalletID);
                
                if ($controlRLimit < $GLOBALS['SEND_LIMIT']) {
                    $messageToSign = $receiverWalletID . $publicWalletID . $timestamp . '1000' . $GLOBALS['SEND_AMOUNT'] . '000';
                    $messageBody = "\"sender\": \"" . $publicWalletID . "\",\"recipient\": \"" . $receiverWalletID . "\",
                    \"type1\": \"" . $GLOBALS['SEND_AMOUNT'] . "\",
                    \"type2\": \"0\",
                    \"type3\": \"0\",
                    \"type4\": \"0\",
                    \"amount\": \"0\",
                    \"sequence\":\"100\",
                    \"timestamp\":\"" . $timestamp . "\",
                    \"text\": \"" . $keywordMessageEncoded . "\"";

                        $publicKey = getPublicKey($userID);
                        $privateKey = getPrivateKey($userID);
                        $signature = getSignature($publicKey, $privateKey, $messageToSign);
                        $result = createTempFinRecord($msisdn, $signature, $messageBody, $receiverName, $receiverPhone);
                        $optionList = getReasonOptions($optionPoll);

                        $anket = '{
                        "txnid":"9999",
                        "receiver":{
                            "type":2,
                            "address": "' . $receiver . '"
                        },
                        "composition":{
                            "list":[
                            {
                                "type":13,
                                "tmmtype":2,
                                "polltmm":{
                                    "title":"' . getNameSuffix($receiverName) . ' teşekkür etmek istedin ve '.$GLOBALS['SEND_AMOUNT'].' IMS yolluyorsun.",
                                    "description":"Arkadaşına hangi mesajı ileteyim? ",
                                    "polltype":0,
                                    "pollid":"reasonList-hizli",
                                    "image":{
                                        "url":"http://timsac.turkcell.com.tr/scontent/p2p/15032018/11/Pc2de09311da2d8e88395bdacec4c53a40b8801012dc80f501c4f4e397e258b318.jpg",
                                        "ratio":1
                                    },
                                    "optionlist":'.$optionList.',
                                    "buttonname":"Yolla"
                                }
                            }
                            ]
                        }
                    }';
                    
                    $result = sendBipResponseIncReceiver($anket);
                } else {
                    sendBipResponseErza("90" . $msisdn, "Maalesef " . getNameSuffix($receiverName) . " bugün 3 gönderim yaptın. Daha fazla teşekkür için yarını bekle :)");    
                }
            } else {
                sendBipResponseErza("90" . $msisdn, "Maalesef bakiyen yetersiz. Biraz da teşekkür almaya bak ya da Pazartesiyi bekle :)");
            }
        } else {
            sendBipResponseErza($receiver, "Çok mu sık teşekkür ediyorsun acaba :) 1 dk beklemen gerekiyor maalesef.");
        }
	} else {
		sendBipResponseErza("90" . $msisdn, "İyi bakalım, bu seferlik öyle olsun :)");
	}
}

if ($ctype == 'Poll' && $pollID == 'reasonList') {
    $reason = getReason($optionPoll);
    $messageBody = getMessageBody($msisdn);
	logr("Poll","debug","messageBody: ".$messageBody);
    if (isset($messageBody)) {
        $signature = getMessageSign($msisdn);
        $publicKey = getPublicKey($userID);
        $privateKey = getPrivateKey($userID);

        $receiverPhone = getMessageReceiverPhone($msisdn);
        $receiverName = getNamebyPhone($receiverPhone);
        $receiverUserID = getuserIDByMSISDN($receiverPhone);
        $receiverWalletID = getWalletID($receiverUserID);
        $receiverBipPhone = '90' . $receiverPhone;
        $controlRLimit = GetReceiverLimit($publicWalletID, $receiverWalletID);

        $senderName = getNamebyPhone($msisdn);
		
		if ($controlRLimit < $GLOBALS['SEND_LIMIT']) {
            $resultCode = transferVcoinWithSign($messageBody, $publicKey, $signature);
            $transactionType = 'bipSendIMS';
            $happyMessage = 'bip jet: ' . $reason;
            createFinancialTransaction($msgId, $publicWalletID, $receiverWalletID, $GLOBALS['SEND_AMOUNT'], $transactionType, $resultCode, $receiverName, $optionPoll);
            //alıcıya da bip mesajı ile bilgi verelim.
            $receiverContent = $reason . "\n\n" . $senderName . " sana ".$GLOBALS['SEND_AMOUNT']." IMS yolladı :) \n\nPuanların HappyChain'de kısa süre içerisinde işlenecek ve bakiyene yansıyacak.";
            $content = getNameSuffix($receiverName). "\n\n" . $reason . "\n\nmesajını da ileterek ".$GLOBALS['SEND_AMOUNT']." IMS transferini yaptık.\n\nAyrıca sen de bu gönderimden 1 IMS kazandın.";
        } else { 
			$content =  getNameSuffix($receiverName) . " bugün 3 gönderim yaptın. Daha fazla teşekkür için yarını bekle :)";
		}
	
		logr("Poll","debug","resultCode:" . $resultCode);
        if(isset($pollIDExt) && $pollIDExt=='hizli'){
            sendBipResponseErza($receiverBipPhone, $receiverContent);
        } else {
            if ($resultCode == '120') {
                $anket = '{
                    "txnid":"'.rand(1000, 20000).'",
                    "receiver":{
                        "type":2,
                        "address": "' . $receiverBipPhone . '"
                    },
                    "composition":{
                        "list":[
                        {
                            "type":13,
                            "tmmtype":2,
                            "polltmm":{
                                "title":"'.$reason . '\n\n' . $senderName . ' sana '.$GLOBALS['SEND_AMOUNT'].' IMS yolladı :)",
                                "description":"Sen de ona karşılık vermek ister misin? :)",
                                "polltype":0,
                                "pollid":"hizlicevap",
                                "optionlist":[{
                                        "optionid":"'. $userID .'",
                                        "name":"Yolla Gitsin"
                                    },
                                    {
                                        "optionid":"0",
                                        "name":"Hayır, zaten bana borcu vardı."}],
                                "buttonname":"Yolla"
                            }
                        }
                        ]
                    }
                }';
                        
                $result = sendBipResponseIncReceiver($anket);
                
            }
        }
    } else { 
		$content = 'Sebep seçimini 2 dakika içinde yapmalısın. geç kaldığın için işlemini iptal ettim. Arkadaşının ismini yazarak yeniden gönderim başlatabilirsin.';
	}
    
}

if ($keywordLT == 'top5XX' || (isset($payloadMessage) && $payloadMessage == 'top5XX')) {
//$receiverList=getReceiverList();
    $tribeID = getTribeID($userID);
    $content = getTop5($tribeID);
}

if ($keywordLT == 'son5giden' || (isset($payloadMessage) && $payloadMessage == 'son5giden')) {
    $content = getLastSent($userID,5);
    if (!isset($content)) {$content = "Henüz gönderim yapmadın.";}
}

if ($keywordLT == 'son5gelen' || (isset($payloadMessage) && $payloadMessage == 'son5gelen')) {
    $content = getLastReceived($userID,5);
    if (!isset($content)) {$content = "Henüz kimseden teşekkür almadın.";}
}

if ($keywordLT == 'pot15' || (isset($payloadMessage) && $payloadMessage == 'pot15')) {
//$receiverList=getReceiverList();
    $content = getTop5('2');
}

if ($keywordLT == 'tranco' || (isset($payloadMessage) && $payloadMessage == 'tranco')) {
    $content = transactionCount();
}

if ($keywordLT == 'topres' || (isset($payloadMessage) && $payloadMessage == 'topres')) {
    $content = getTopReasons();
}

if ($keywordLT == 'liste' || (isset($payloadMessage) && $payloadMessage == 'liste')) {
    $tribeID = getTribeID($userID);
    $tribeName = getTribeName($tribeID);
    $receiverList = getReceiverList($userID,$tribeID);
    $receiverList = $tribeName . " - Alıcı Listesi\n" . $receiverList;
	sendBipResponseErza($receiver, $receiverList);
    //$receiverList2 = getReceiverListP2($tribeID);
    //$contentP1 = $tribeName . "\n\n" . $receiverList1;
    //$content = $receiverList2;
}

if ($keywordLT == 'full' || (isset($payloadMessage) && $payloadMessage == 'full')) {
    $receiverList = getReceiverListFull($tribeID);
    $content = $receiverList;
}

if ($keywordLT == 'menu') {
    sendQuickMenu($receiver);
}

if ($keywordLT == 'anket' || (isset($payloadMessage) && $payloadMessage == 'anket')) {
    //sendReceiverPoll($receiver);
    $content = "Aktif anketim yok, olunca haber veririm.";
}

if ($keywordLT == 'jet' || (isset($payloadMessage) && $payloadMessage == 'jet')) {
    $tnxid = rand(1000, 20000);
    //$content=sendReceiverPollFromDB($receiver);
    $myList = getPollReceiverlist($userID);
    if ($myList == '') {$content = "Hızlı gönder menüne arkadaşlarını eklemelisin. Liste yazarak arkadaşlarının HappyID'lerini gör. Ardından \"Ekle HappyID\" yazarak arkadaşını listene ekle.\n\nÖrnek: Ekle CIH2216";}

    $anket = '{
     "txnid":"' . $tnxid . '",
     "receiver":{
        "type":2,
        "address": "' . $receiver . '"
     },
     "composition":{
        "list":[
           {
              "type":13,
              "tmmtype":2,
              "polltmm":{
                 "title":"Hemen '.$GLOBALS['SEND_AMOUNT'].' IMS Yolla",
                 "description":"Kime göndermek istersin?",
                 "polltype":0,
                 "pollid":"ASDFK-2",
                 "image":{
                    "url":"http://timsac.turkcell.com.tr/scontent/p2p/19022018/09/Pe336b30c03db3493052cdede73334c1b57443c13c219e3b7d70441d99add1e0d7.png",
                    "ratio":1
                 },
                 "optionlist":[
                   {
                      "optionid":900,
                      "name":"Rasgele"
                   }' . $myList . '
                 ],
                 "buttonname":"Yolla"
              }
           }
        ]
     }
  }';

    $result = sendBipResponseIncReceiver($anket);

}

//şifre resdetleme
if ($keywordLT == 'sifre') {
    $passwd = $keywordRT;
    if ($keywordRT == '') {$content = "Şifre girmedin. Şifreni değiştirmek istiyorsan Sifre YENISIFRE yaz gönder. \nÖrnek: Sifre YeniS1fr3 ";} else {
        $result = updatePassword($userID, $passwd);
        $content = "Şifreniz degistirildi.\n\nŞifren: " . $passwd . "\n\n http://happychain.ga \n\nGüvenliğin için bu mesajı sil. ";}
}

//manual puan transferi
if ($keywordLT == 'yolla') {
    //ikinci kelime alıcı bilgisi
    $receiverAlias = $keywordRT;
    $receiverName = getReceiverName($receiverAlias);
    $senderName = getNamebyPhone($msisdn);
    //üçüncü parametre miktar
    $amount = $keywordP3;

    //geçerli alıcı mı kontrolü
    if (!isset($receiverAlias) || !isset($keywordP3)) {$content = "Alıcı ismini yada puan miktarını girmeyi unuttun. Yardım yazarak nasıl puan göndereceğini öğrenebilirsin.";} else {
        $control = controlReceiver($receiverAlias);
        //alıcı geçerli mi kontrol edelim
        if ($control == 1) {
            $receiverWalletID = getReceiverWalletID($receiverAlias);
            $amount = $keywordP3;
            $messageToSign = $receiverWalletID . $publicWalletID . $timestamp . '1000' . $amount . '000';
            $messageBody = "\"sender\": \"" . $publicWalletID . "\",\"recipient\": \"" . $receiverWalletID . "\",
    \"type1\": \"" . $amount . "\",
    \"type2\": \"0\",
    \"type3\": \"0\",
    \"type4\": \"0\",
    \"amount\": \"0\",
    \"sequence\":\"100\",
    \"timestamp\":\"" . $timestamp . "\",
    \"text\": \"" . $keywordMessageEncoded . "\"";

            //echo '<hr/>imzalanacak metin: '.$messageToSign;
            $publicKey = getPublicKey($userID);
            $privateKey = getPrivateKey($userID);
            //echo '<hr/><b></br> pub:</b> '.$publicKey.'</br><b> prv: </b>'.$privateKey.'</br><b> message To Be Sgined:</b> '.$messageToSign;
            $signature = getSignature($publicKey, $privateKey, $messageToSign);
            //$signature='imzaladim';
            $resultCode = transferVcoinWithSign($messageBody, $publicKey, $signature);
            $result = getResultDescription($resultCode);
            $transactionType = 'bipSendIMS';
            $happyMessage = 'bip: ' . strtoupper($receiverAlias) . " message: " . $keywordMessage;
            createFinancialTransaction($msgId, $publicWalletID, $receiverWalletID, $amount, $transactionType, $resultCode, $happyMessage, $receiverName);
            $receiverPhone = '90' . getPhonebyAlias($receiverAlias);
            //alıcıya da bip mesajı ile bilgi verelim.
            $receiverContent = $senderName . " sana " . number_format($amount) . " IMS yolladı :) \n\nPuanların HappyChain'de kısa süre içerisinde işlenecek ve bakiyene yansıyacak.\n\n" . $keywordMessage . "\n\n" . $resultCode;
            //miktar sayısal değer mi kontrolü yapalım bu da doğruysa alıcıya da mesaj gönderelim.
            if ($resultCode == '120') {
				sendBipResponseErza($receiverPhone, $receiverContent);
			}
            $content =  getNameSuffix($receiverName) . " yollamak istediğin miktar " . number_format($amount) . " IMS. \n\n" . $result . "\n\n" . $keywordMessage;
            //."\n\n alici msisdn: ".$receiverPhone."\n mesaj: ".$receiverContent;
        } else {
            $content = "Alıcıya ait HappyID hatalı. Liste yazarak arkadaşlarının HappyID'lerini görebilirsin.";
        }

        //gönderilen puan geçerli bir değer mi kontrol edelim. değilse hata mesajı basalım
        if (!is_numeric($amount)) {$content = "Göndermek istediğiniz tutar hatalı. Lütfen numerik değer giriniz.\n\n 3 IMS yollamak için örnek mesaj:\n\n Yolla CIH2216 3";}}
}

//content bitis

if (isset($content)) {
	$postResult = sendBipResponseErza($receiver, $content);
}

/*
if(isset($resultCode) && $resultCode === "120" ){
	sleep(4);
	$ext_content =  getNameSuffix($receiverName) . " teşekkür ettin ve 1 IMS kazandın.👏👏👏\nKazandığın puan HappyChain'de transfer işlemin ile aynı bloğa işlenerek hesabına yansıtılacak.";
	sendBipResponseErza($receiver, $ext_content);
}
*/

//date_default_timezone_set('Europe/Istanbul');
//echo "\n\nINFO - ".date('d/m/Y h:i:s', time())." - receiver is ".$receiver." and  message is:\n ".$content."\n\n";
//echo "\n\nINFO - POSTRESULT : ".date('d/m/Y h:i:s', time())." - \n".$postResult;

function sendBipResponseErza($receiver, $content)
{
    $tnxid = rand(1000, 9999);
    $postdata['txnid'] = $tnxid;
    $receiverArray['type'] = 2;
    $receiverArray['address'] = $receiver;
    $postdata['receiver'] = $receiverArray;
    $listArray0['type'] = 0;
    $listArray0['message'] = $content;
    $listArray[0] = $listArray0;
    $composition0['list'] = $listArray;
    $postdata['composition'] = $composition0;
//echo "\npostdata array: ".$postdata;
    //$postdataJson = "json=".json_encode($postdata)."&";
    $postdataJson = json_encode($postdata);
//echo "\n\npostdata json: ".$postdataJson."\n\n\n";
    $result = sendBipResponseIncReceiver($postdataJson);
	return $result;
}


function write_log($log){
	$log = $log . PHP_EOL;
	$file = "/home/serhat/dasHappyChain/log/msChainBip.log";
    file_put_contents($file, $log, FILE_APPEND | LOCK_EX);
}

function sendQuickMenu($receiver)
{
//$tnxid=rand(10000,99999);
    $postdata = '{
     "txnid":"85955",
     "receiver":{
        "type":2,
        "address": "' . $receiver . '"
     },
  "composition":{
        "list":[
           {
              "type":13,
              "tmmtype":3,
              "quickreplytmm":{
                 "postbackid":"ASDF",
                 "buttonlist":[
                    {
                       "type":"1",
                       "name":"💰 IMS Bakiyem",
                       "payload":"puan"
                    },
                    {
                         "type":"1",
                         "name":"➡️ Son Yolladıklarım",
                         "payload":"son5giden"
                     },
                    {
                       "type":"1",
                       "name":"⬅️ Son gelenler",
                       "payload":"son5gelen"
                    },
                    {
                       "type":"1",
                       "name":"👤👤 Alıcı Listesi",
                       "payload":"Liste"
                    },
                    {
                       "type":"1",
                       "name":"❓ Nasıl IMS Yollarım",
                       "payload":"nasil"
                    },
    {
                     "type":"1",
                     "name":"🔮 Sihirli Kelimeler",
                     "payload":"yardim"
                  	}
                 ]
              }
           }
        ]
     }
  }';

    $result = sendBipResponseIncReceiver($postdata);
//return $result."POSTDATA: ".$postdata;
    return $result;
//$content=$postdata;
}

function sendBipResponseIncReceiver($content)
{
    $bipTesURL = "http://tims.turkcell.com.tr/tes/rest/spi/sendmsgserv";
    $username = "bu2705615192872148";
    $password = "1020velo";
    $ch = curl_init($bipTesURL);
    curl_setopt($ch, CURLOPT_HEADER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array("Content-Type: application/json"));
    curl_setopt($ch, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
    curl_setopt($ch, CURLOPT_USERPWD, "bu2705615192872148:1020velo");
    curl_setopt($ch, CURLOPT_POSTFIELDS, $content);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    $result = curl_exec($ch);
    return $result;

}

function logr($loc, $severity, $log){
	if(array_keys($GLOBALS['LOG_LEVELS'],$severity)[0] <= array_keys($GLOBALS['LOG_LEVELS'],$GLOBALS['LOG_LEVEL'])[0]){		
		$log=date("Y-m-d h:i:sa")." - HANDLER - ".$severity." - ".$loc." - ".$log . PHP_EOL;
		file_put_contents("/home/serhat/dasHappyChain/happychain.log", $log, FILE_APPEND | LOCK_EX);
	}
}

function clean_buffer(){
	if (ob_get_contents()) ob_end_clean();
}
