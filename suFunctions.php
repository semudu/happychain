<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$GLOBALS['sendCoinURL']='http://localhost:6001/transactions/new';
$GLOBALS['getBalanceURL']='http://localhost:6001/balance';

$GLOBALS['dbname'] = 'happychain';
$GLOBALS['projectID'] = '0';


function getConnection(){
	$servername = 'localhost';
	$username = 'happychain';
	$password = '12#happy34#CHAIN';
	
	
	$conn = new mysqli($servername, $username, $password, $GLOBALS['dbname']);
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
	}
	$conn->set_charset('utf8');
	return $conn;
}

function getRandomReceiver($tribeID, $userID)
{
    $sql = "select userID from adressBook where tribeID=" . $tribeID . " and userID!='" . $userID . "' and projectID=".$GLOBALS['projectID']." order by rand() limit 1;";
    $conn = getConnection();
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $userID = $row["userID"];
        }
        $conn->close();
        return $userID;
    }

}

function getTop5($tribeID)
{
    $sql="SELECT a.receiverAlias alias, ( a.received_count*10 + b.sender_count ) AS total, b.sender_count as scount, a.received_count as rcount FROM 
        ( SELECT ft.receiverAlias, COUNT(1) AS received_count FROM ".$GLOBALS['dbname'].".financial_transaction ft 
        WHERE ft.result = '120' AND ft.is_active = 1 
        GROUP BY ft.receiverAlias ) a, 
        ( SELECT ab.alias AS senderAlias, COUNT(1) AS sender_count 
        FROM financial_transaction ft, adressBook ab 
        WHERE ft.sender = ab.receiverWalletID AND ft.is_active = 1 AND ft.result = '120' GROUP BY ab.alias ) b 
        WHERE a.receiverAlias = b.senderAlias ORDER BY total DESC limit 15;";

    $top5 = "İsim - Toplam - Gönderdiği - Aldığı\n\n";
    $i = 1;
    $conn = getConnection();
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            $amount = number_format($row["total"]);
            $adet = $row["rcount"];
            $gonderim = $row["scount"];
            $top5 = $top5 . $i . ") " . $alias . " : Toplam " . $amount . " IMS\nAldığı teşekkür: " . $adet . ", Ettiği teşekkür: " . $gonderim . "\n\n";
            $i = $i + 1;
        }
        $conn->close();
    }
    return $top5;

}

function getLastSent($userID,$limit)
{
    $sql = 'select ft.receiverAlias as alias, r.reason as reason, date_format(ft.createDate,"%d %M, %W") date
			from financial_transaction ft,reason r where sender in (select publicKey from wallet where userID=' . $userID . ')
			and r.id = ft.reasonID
			and ft.result=120
			and ft.is_active = 1
			order by transID desc
			limit '.$limit;
    
    $msg = "Gönderdiğin son ".$limit." mesaj \n\n";
    $conn = getConnection();
	$conn->set_charset('utf8mb4');
	setMysqlLcNamesTR($conn);
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            $reason = $row["reason"];
			$date = $row["date"];
            $msg = $msg . $alias . "\n" . $date . "\n" . $reason . "\n\n";
        }
        $conn->close();
        return $msg;

    }

}

function setMysqlLcNamesTR($conn){
	$conn->query("SET lc_time_names = 'tr_TR'");
}

function getTotalSentIsActive($publicWalletID)
{
    $sql = "select sum(amount) as amount
			from financial_transaction
			where sender = '".$publicWalletID."'
			and transactionType='bipSendIMS'
			and result=120
			and is_active = 1";
    
    $conn = getConnection();
    $result = $conn->query($sql);
    
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $amount = number_format($row["amount"]);
        }
        $conn->close();
        return $amount;
    }
}

function getTotalSentCount($publicWalletId)
{
    $sql = "select count(sender) as amount
			from financial_transaction where sender ='".$publicWalletId."'
			and result=120";
    
    $conn = getConnection();
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $amount = number_format($row["amount"]);
        }
        $conn->close();
        return $amount;
    }

}

function getLastReceived($userID,$limit)
{
    $sql = 'select ab.alias as alias, r.reason, date_format(ft.createDate,"%d %M, %W") date
from financial_transaction ft,  adressBook ab, reason r
where ft.sender = ab.receiverWalletID
and ft.reasonID = r.id
and ft.receiver in (select publicKey from wallet where userID=' . $userID . ')
and ft.result=120
and ft.is_active = 1
order by ft.transID desc
limit '.$limit;
    
    $msg = "Sana gönderilen son ".$limit." mesaj\n\n";
    $conn = getConnection();
	$conn->set_charset('utf8mb4');
	setMysqlLcNamesTR($conn);
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            $reason = $row["reason"];
            $date = $row["date"];
            $msg = $msg . $alias . "\n" . $date . "\n" . $reason . "\n\n";
        }
        $conn->close();
        return $msg;
    }

}

function getTotalReceivedIsActive($userID)
{
    $sql = "select sum(ft.amount) as amounto
			from financial_transaction ft,  adressBook ab
			where ft.receiver = ab.receiverWalletID
			and  ab.userID=" . $userID . "
			and ft.result=120
			and ft.transactionType='bipSendIMS'
			and ft.is_active = 1";

	$bonus = getTotalSentCount($userID);
    $conn = getConnection();
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $amount = number_format($row["amounto"]);

        }
        $conn->close();
        $totalGelen = $amount + $bonus;
        return $totalGelen;
    }

}

function getuserIDByMSISDN($msisdn)
{
	if(strlen($msisdn)>10){
		$msisdn = substr($msisdn,-10);
	}
    
    $conn = getConnection();
    $sql = "select userID from " . $GLOBALS['dbname'] . ".user where phone='" . $msisdn . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $userID = $row["userID"];
        }
        $conn->close();
        return $userID;
    }
}

function getPollReceiverlist($userID)
{
    $sql = "select concat(',
						{
							\"optionid\":',userID,',
							\"name\":\"',alias,'\"
						}') as receiverPoll from adressBook where projectID=".$GLOBALS['projectID']." and userID in (select receiverUserID from " . $GLOBALS['dbname'] . ".shortcut where userID='" . $userID . "') order by createDate desc limit 5;";
    
    $receiverList = '';
    $conn = getConnection();
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $receiverList = $receiverList . $row["receiverPoll"];
        }
        $conn->close();
        return $receiverList;
    }
}

function getPollReceiverlistShort($key, $tribeID)
{
    $sql = "select concat(',
							{
								\"optionid\":',userID,',
								\"name\":\"',alias,'\"
							}') as receiverPoll from adressBook where projectID=".$GLOBALS['projectID']." and upper(alias) like upper('" . $key . "%') and tribeID='" . $tribeID . "' order by createDate desc limit 4;";

    $sql2 = "select concat(',
							{
								\"optionid\":',adressBook.userID,',
								\"name\":\"',adressBook.alias,'\"
							}') as receiverPoll
                            from adressBook ,
(select * from
(SELECT userID, SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 1), ' ', -1) AS first_name,
   If(  length(alias) - length(replace(alias, ' ', ''))>1,
       SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 2), ' ', -1) ,NULL)
           as middle_name,
   SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 3), ' ', -1) AS last_name
FROM adressBook) as namelist
where upper(first_name) like upper('" . $key . "%')
or upper(middle_name) like upper('" . $key . "%') ) as ss
where adressBook.userID=ss.USERID
and adressBook.tribeID='" . $tribeID . "'
and adressBook.projectID=".$GLOBALS['projectID']."
order by adressBook.createDate desc limit 4;";

    
    $receiverList = '';
    $conn = getConnection();
    $result = $conn->query($sql2);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $receiverList = $receiverList . $row["receiverPoll"];
        }
        $conn->close();
        return $receiverList;
    }

}

function getPollReceiverlistLong($key, $tribeID)
{
    $sql = "select concat('
							{
								\"optionid\":',adressBook.userID,',
								\"name\":\"',adressBook.alias,'\"
							}') as receiverPoll from adressBook where projectID=".$GLOBALS['projectID']." and upper(alias)
							like upper('" . $key . "%') and tribeID='" . $tribeID . "' order by createDate desc limit 4;";

    $sql2 = "select concat('
							{
								\"optionid\":',adressBook.userID,',
								\"name\":\"',adressBook.alias,'\"
							}') as receiverPoll
						                            from adressBook ,
						(select * from
						(SELECT userID, SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 1), ' ', -1) AS first_name,
						   If(  length(alias) - length(replace(alias, ' ', ''))>1,
						       SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 2), ' ', -1) ,NULL)
						           as middle_name,
						   SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 3), ' ', -1) AS last_name
						FROM adressBook) as namelist
						where upper(first_name) like upper('" . $key . "%')
						or upper(middle_name) like upper('" . $key . "%') ) as ss
						where adressBook.userID=ss.USERID
                                                and adressBook. projectID=".$GLOBALS['projectID']."
						and adressBook.tribeID='" . $tribeID . "'
						order by adressBook.createDate desc limit 4;";

    
    $receiverList = '';
    $i = 0;
    $conn = getConnection();
    $result = $conn->query($sql2);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            if ($i == 0) {$receiverList = $row["receiverPoll"];}
            if ($i > 0) {$receiverList = $receiverList . ',' . $row["receiverPoll"];}
            $i = $i + 1;
        }
        $conn->close();
        return $receiverList;
    }

}

function getPollReceiverlistCount($key, $tribeID)
{
    $sql = "select  count(alias) as adet from adressBook where projectID=".$GLOBALS['projectID']." and upper(alias) like upper('" . $key . "%') and tribeID='" . $tribeID . "';";
    $sql2 = "select count(adressBook.alias) as adet from adressBook ,
	(select * from
	(SELECT userID, SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 1), ' ', -1) AS first_name,
	 If(  length(alias) - length(replace(alias, ' ', ''))>1,
			 SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 2), ' ', -1) ,NULL)
					 as middle_name,
	 SUBSTRING_INDEX(SUBSTRING_INDEX(alias, ' ', 3), ' ', -1) AS last_name
	FROM adressBook) as namelist
	where upper(first_name) like upper('" . $key . "%')
	or upper(middle_name) like upper('" . $key . "%') ) as ss
	where adressBook.projectID=".$GLOBALS['projectID']." and adressBook.userID=ss.USERID
	and adressBook.tribeID='" . $tribeID . "'";
    
    $receiverList = '';
    $conn = getConnection();
    $result = $conn->query($sql2);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $receiverListCount = $row["adet"];
        }
        $conn->close();
        return $receiverListCount;
    }

}

function getReceiverName($receiverAlias)
{
    
    $conn = getConnection();
    $sql = "select alias from " . $GLOBALS['dbname'] . ".adressBook where receiverAlias=upper('" . $receiverAlias . "');";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $receiverName = $row["alias"];
        }
        $conn->close();
        return $receiverName;
    }
}

function getWalletID($userID)
{
    
    $conn = getConnection();
    $sql = "select walletID,publicKey from " . $GLOBALS['dbname'] . ".wallet where userID='" . $userID . "'";
    //echo $sql;
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $publicWalletID = $row["publicKey"];
        }

        $conn->close();
        return $publicWalletID;
    }

}

function getReceiverWalletID($receiverAlias)
{
    
    $conn = getConnection();
    $sql = "select walletID, publicKey from " . $GLOBALS['dbname'] . ".wallet where
userID in (select userID from " . $GLOBALS['dbname'] . ".adressBook where receiverAlias=upper('" . $receiverAlias . "'))";
    //echo $sql;
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $publicWalletID = $row["publicKey"];
        }

        $conn->close();
        return $publicWalletID;
    }

}

function getReceiverNamebyUserID($userID)
{
    $conn = getConnection();
	$conn->set_charset('utf8');
	
	$sql = "select alias from " . $GLOBALS['dbname'] . ".adressBook where userID='" . $userID . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $receiverName = $row["alias"];
        }
        $conn->close();
		logr("getReceiverNamebyUserID","info","isim: ".$receiverName);
        return $receiverName;
    }

}

function getTribeID($userID)
{
    
    $conn = getConnection();
    $sql = "select tribeID from " . $GLOBALS['dbname'] . ".adressBook where projectID=".$GLOBALS['projectID']." and userID='" . $userID . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $tribeID = $row["tribeID"];
        }
        $conn->close();
        return $tribeID;
    }

}

function getPhonebyUserID($userID)
{
    
    $conn = getConnection();
    $sql = "select phone from " . $GLOBALS['dbname'] . ".adressBook where userID='" . $userID . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $receiverPhone = $row["phone"];
        }
        $conn->close();
        return $receiverPhone;
    }

}

function getTribeName($tribeID)
{
    $conn = getConnection();
    $sql = "select tribeName from " . $GLOBALS['dbname'] . ".tribe where id='" . $tribeID . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $tribeName = $row["tribeName"];
        }
        $conn->close();
        return $tribeName;
    }

}

function updatePassword($userID, $passwd)
{
    $conn = getConnection();
    $sql = "update " . $GLOBALS['dbname'] . ".user set passwd=md5('" . $passwd . "') where userID='" . $userID . "'";
    //echo $sql;
    $result = $conn->query($sql);

    $conn->close();
    return $result;
}

function getReceiverList($userID, $tribeID)
{
    
    $receiverList = "";
    $conn = getConnection();
    //$sql = "select * from " . $GLOBALS['dbname'] . ".adressBook  where projectID=".$GLOBALS['projectID']." and tribeID=" . $tribeID . " and alias<'M' order by alias;";
	$sql = "select * from " . $GLOBALS['dbname'] . ".adressBook  where projectID=".$GLOBALS['projectID']." and tribeID=" . $tribeID . " and userID != " . $userID . " order by alias;";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            //$receiverAlias=$row["receiverAlias"];
            $receiverList = $receiverList . "\n" . $alias;
        }
        $conn->close();
        return $receiverList;
    }
}
/*
function getReceiverListP2($tribeID)
{
    
    $receiverList = "MsHappyChain Kullanıcı Listesi\n";
    $conn = getConnection();
    $sql = "select * from " . $GLOBALS['dbname'] . ".adressBook where projectID=".$GLOBALS['projectID']." and tribeID=" . $tribeID . "  and  alias>'M'  order by alias;";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            //$receiverAlias=$row["receiverAlias"];
            $receiverList = $receiverList . "\n" . $alias;
        }
        $conn->close();
        return $receiverList;
    }
}
*/
function getReceiverListFull($tribeID)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $i = 0;
    $conn = getConnection();
    $sql = "select * from " . $GLOBALS['dbname'] . ".adressBook order by alias;";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            $receiverAlias = $row["receiverAlias"];
            $i = $i + 1;
            $receiverList = $receiverList . "\n" . $i . "- " . $alias . " - " . $receiverAlias;
        }
        $conn->close();
        return $receiverList;
    }
}

function getRecentActivities()
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = "----";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            $receiverAlias = $row["receiverAlias"];
            $receiverList = $receiverList . "\n" . $alias . " - " . $receiverAlias;
        }
        $conn->close();
        return $receiverList;
    }
}

function getNamebyPhone($msisdn)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = "select alias from " . $GLOBALS['dbname'] . ".adressBook where phone='" . $msisdn . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
        }
        $conn->close();
        return $alias;
    }

}

function controlReceiver($receiverAlias)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = "select count(1) as adet from " . $GLOBALS['dbname'] . ".adressBook where receiverAlias='" . $receiverAlias . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["adet"];
        }
        $conn->close();
        return $alias;
    }

}

function getPhonebyAlias($receiverAlias)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = "select phone from " . $GLOBALS['dbname'] . ".adressBook where projectID=".$GLOBALS['projectID']." and receiverAlias=upper('" . $receiverAlias . "');";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $phone = $row["phone"];
        }
        $conn->close();
        return $phone;
    }

}

function getuserIDbyAlias($receiverAlias)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = "select userID from " . $GLOBALS['dbname'] . ".adressBook where projectID=".$GLOBALS['projectID']." and receiverAlias=upper('" . $receiverAlias . "');";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $userID = $row["userID"];
        }
        $conn->close();
        return $userID;
    }

}

function getMessageBody($sender)
{
	logr("getMessageBody","info","sender: ".$sender);
    $conn = getConnection();
    $sql = "select * from happychain.financial_temp where userID='" . $sender . "' and status=0
			 and id in (select max(id) from happychain.financial_temp where userID='" . $sender . "' )
			 and   createDate>date_sub(now(), interval 2 minute)";
    
    $result = $conn->query($sql);
    logr("getMessageBody","info","sql: ".$sql);
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $messageBody = $row["messageBody"];
		}
        $conn->close();
        return $messageBody;
    }
}

function getMessageSign($sender)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = " select * from " . $GLOBALS['dbname'] . ".financial_temp where userID='" . $sender . "' and status=0
 and id in (select max(id) from " . $GLOBALS['dbname'] . ".financial_temp where userID='" . $sender . "' )
 and   createDate>date_sub(now(), interval 2 minute)";
    //$sql = " select reasonDescription from " . $GLOBALS['dbname'] . ".reason where id=".$optionID.";";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $userID = $row["signature"];
        }
        $conn->close();
        return $userID;
    }

}

function getMessageReceiverPhone($sender)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = " select * from " . $GLOBALS['dbname'] . ".financial_temp where userID='" . $sender . "' and status=0
 and id in (select max(id) from " . $GLOBALS['dbname'] . ".financial_temp where userID='" . $sender . "' )
 and   createDate>date_sub(now(), interval 2 minute)";
    //$sql = " select reasonDescription from " . $GLOBALS['dbname'] . ".reason where id=".$optionID.";";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $userID = $row["receiverPhone"];
        }
        $conn->close();
        return $userID;
    }

}

function getMessageReceiverName($sender)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = " select receiverName from " . $GLOBALS['dbname'] . ".financial_temp where userID='" . $sender . "' and status=0
 and id in (select max(id) from " . $GLOBALS['dbname'] . ".financial_temp where userID='" . $sender . "' )
 and   createDate>date_sub(now(), interval 2 minute)";
    //$sql = " select reasonDescription from " . $GLOBALS['dbname'] . ".reason where id=".$optionID.";";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $userID = $row["receiverName"];
        }
        $conn->close();
        return $userID;
    }

}

function getReason($optionID)
{
    $conn = getConnection();
    $conn->set_charset('utf8mb4');
	$sql = " select reason from " . $GLOBALS['dbname'] . ".reason where id=" . $optionID . ";";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $reason = $row["reason"];
        }
        $conn->close();
        return $reason;
    }

}

function createTempFinRecord($sender, $signature, $messageBody, $receiverName, $receiverPhone)
{
    
    $conn = getConnection();
    $sql = "INSERT INTO " . $GLOBALS['dbname'] . ".`financial_temp`
		(`userID`, `messageBody`, `signature`,`status`,`receiverName`,`receiverPhone`)
		VALUES ('" . $sender . "', '" . $messageBody . "', '" . $signature . "', '0','" . $receiverName . "','" . $receiverPhone . "');";
    
	logr("createTempFinRecord","info","sql: ".$sql);
    if ($conn->query($sql) === true) {
        //echo "</br>INFO: New record created successfully";
    } else {
        echo "Error: " . $sql . "<br>" . $conn->error;
    }
    $conn->close();
}

function createFinancialTransaction($sessionTransactionID, $sender, $receiver, $amount, $transactionType, $result, $receiverAlias, $reasonId)
{
    
    $conn = getConnection();

    
    $sql = "INSERT INTO happychain.`financial_transaction`
	(`sessionTransactionID`, `sender`, `receiver`,`amount`, `transactionType`,`result`,`receiverAlias`,`reasonID`)
	VALUES ('" . $sessionTransactionID . "', '" . $sender . "', '" . $receiver . "', '" . $amount . "', '" . $transactionType . "', '" . $result . "', '" . $receiverAlias . "', " . $reasonId . ");";
    logr("createFinancialTransaction","info","sql: ".$sql);
    if ($conn->query($sql) === true) {
        logr("createFinancialTransaction","info","transaction created.");
    } else {
        logr("createFinancialTransaction","info","sql error: ".$conn->error);
    }
    $conn->close();
}

function createShortcut($userID, $receiverUserID)
{
    
    $conn = getConnection();

    //$sessionTransactionID,$sender,$receiver,$amount,$transactionType,$result
    $sql = "INSERT INTO " . $GLOBALS['dbname'] . ".`shortcut`
	(`userID`, `receiverUserID`)
	VALUES ('" . $userID . "', '" . $receiverUserID . "');";
    echo $sql;
    if ($conn->query($sql) === true) {
        //echo "</br>INFO: New record created successfully";
    } else {
        echo "Error: " . $sql . "<br>" . $conn->error;
    }
    $conn->close();
}

function getResultDescription($resultCode)
{
    
    $receiverList = "Alıcı ismi - HappyID\n";
    $conn = getConnection();
    $sql = "select resultDescription from " . $GLOBALS['dbname'] . ".resultcodes where typeID=1 and resultCode='" . $resultCode . "';";
    $result = $conn->query($sql);
    //echo '</br>LOG: sql:'.$sql;
    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $reasonDescription = $row["resultDescription"];
        }
        $conn->close();
        return $reasonDescription;
    }

}

function getIMSBalance($publicWalletID)
{
    $postdata['wallet'] = $publicWalletID;
    $postdataJson = json_encode($postdata);
    //echo '</br>LOG: '.$postdataJson;

    $ch = curl_init($GLOBALS['getBalanceURL']);
    curl_setopt($ch, CURLOPT_HEADER, false);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array("Content-Type: application/json"));
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postdataJson);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    $result = curl_exec($ch);
    //echo '</br>result</br>' ;
    //print_r($result);
    $balanceJson = json_decode($result, true);
    //echo '</br>resp json</br>'.$balanceJson ;
    //print_r($balanceJson);
    $balance = $balanceJson['Type1'];
    return $balance;
}

function getFullBalanceList()
{

    $sql = "select userID, alias, receiverWalletID, phone from adressBook
where tribeID=2 order by alias asc";
    
	$conn = getConnection();
    //$sql = "select RSApublic from " . $GLOBALS['dbname'] . ".wallet where userID='".$userID."';";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $alias = $row["alias"];
            $userID = $row["userID"];
            $publicWalletID = $row["receiverWalletID"];
            $bakiye = getIMSBalance($publicWalletID);
            if ($bakiye == 0) {$html = '<font size="3" color="red">';} else { $html = '<font size="3" color="green">';}
            $note = $html . $userID . " - " . $alias . ' - ' . $publicWalletID . " - " . $bakiye . "</font></br>";
            echo $note;
        }
        $conn->close();
        //if ($totalAmount<$limit) {return 1;} else {return 0;}
    }

}

function controlLimit()
{
    $limit = 1000000000000000;
    $sql = "select sum(amount) as totalAmount from financial_transaction where result=120 and createDate> (select date(curdate() - interval weekday(curdate()) day))";
    
    $conn = getConnection();
    //$sql = "select RSApublic from " . $GLOBALS['dbname'] . ".wallet where userID='".$userID."';";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $totalAmount = $row["totalAmount"];
        }
        $conn->close();
        if ($totalAmount < $limit) {return 1;} else {return 0;}
    }
}

function GetReceiverLimit($publicWalletID, $receiverWalletID)
{
    $sql = "select count(1) as adet from financial_transaction
 where sender='" . $publicWalletID . "'
 and receiver='" . $receiverWalletID . "'
 and result=120
 and date(createDate) = curdate();";
    
 $conn = getConnection();

    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $adet = $row["adet"];
        }
        $conn->close();
        return $adet;
    }
}

function transferVcoinWithSign($messageToSign, $publicKey, $signature)
{
    $controlLimit = controlLimit();
    if ($controlLimit == 1) {
        $content = "{\n \"message\": {" . $messageToSign . "},\n \"publicKey\": \"" . $publicKey . "\",\n \"signature\": \"" . $signature . "\"}";

        //echo '<hr/></br><b>TRANSFER REQUEST CONTENT JSON :</b> '.$content;
		logr("transferVcoinWithSign","info","request: ".$content);
		
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $GLOBALS['sendCoinURL']);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $content);
        curl_setopt($ch, CURLOPT_POST, 1);

        $headers = array();
        $headers[] = "Content-Type: application/json";
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        $result = curl_exec($ch);

        if (curl_errno($ch)) {
            echo '</br> HTTP Error:' . curl_error($ch);
        }
        curl_close($ch);

        $transferJson = json_decode($result, true);
        //$returnMessage='HappyChain mesajı: '.$transferJson['message'];
		logr("transferVcoinWithSign","info","response: ".$result);
        $returnMessage = $transferJson['resultcode'];
        return $returnMessage;
    } else {
        return 911;
    }

}

function getSignature($publicKey, $privateKey, $message)
{
    $command2 = "python3 /home/serhat/dasHappyChain/interface/Generate_PK.py Sign '" . $message . "' '" . $publicKey . "' '" . $privateKey . "'";
    echo '<hr/><b>Signature Command:</b> ' . $command2;
    $run2 = system($command2, $retval2);
    $response2 = json_decode($run2, true);
    $signature = $response2['signature'];
    echo '<hr/> signature: ' . $signature;
    return $signature;

}

function getPublicKey($userID)
{
    
    $conn = getConnection();
    $sql = "select RSApublic from " . $GLOBALS['dbname'] . ".wallet where userID='" . $userID . "';";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $publicKey = $row["RSApublic"];
        }
        $conn->close();
        return $publicKey;
    }

}

function getPrivateKey($userID)
{
    
    $conn = getConnection();
    $sql = "select RSAprivate from " . $GLOBALS['dbname'] . ".wallet where userID='" . $userID . "';";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $publicKey = $row["RSAprivate"];
        }
        $conn->close();
        return $publicKey;
    }

}

function cashBack($msgId, $receiverWalletID)
{
    $cashBackWalletID = '14D5RfBnj1BCnS5WeL4rQgqAcjttiBKSQ6';
    $cashbackUserID = 1;
    $amount = 1;
    $messageToSign = $receiverWalletID . $cashBackWalletID . $timestamp . '1000' . $amount . '000';
    $messageBody = "\"sender\": \"" . $cashBackWalletID . "\",\"recipient\": \"" . $receiverWalletID . "\",
	\"type1\": \"" . $amount . "\",
	\"type2\": \"0\",
	\"type3\": \"0\",
	\"type4\": \"0\",
	\"amount\": \"0\",
	\"sequence\":\"100\",
	\"timestamp\":\"" . $timestamp . "\"";

    //echo '<hr/>imzalanacak metin: '.$messageToSign;
    $publicKey = getPublicKey($cashbackUserID);
    $privateKey = getPrivateKey($cashbackUserID);
    //echo '<hr/><b></br> pub:</b> '.$publicKey.'</br><b> prv: </b>'.$privateKey.'</br><b> message To Be Sgined:</b> '.$messageToSign;
    $signature = getSignature($publicKey, $privateKey, $messageToSign);
    //$signature='imzaladim';
    $resultCode = transferVcoinWithSign($messageBody, $publicKey, $signature);
    createFinancialTransaction($msgId, $cashBackWalletID, $receiverWalletID, number_format($amount), 'cashBack', $resultCode, 'cashBack', '');
    //$result=getResultDescription($resultCode);
    return $resultCode;

}

function getReasonOptions($receiverId){
	$conn = getConnection();
    $sql = "select distinct r.id, r.reason, r.gender from " . $GLOBALS['dbname'] . ".reason r, " . $GLOBALS['dbname'] . ".user u 
            where r.active = 1 and u.userID = ". $receiverId . " 
            and (r.gender = u.gender or r.gender is null) order by r.gender desc, r.id asc limit 6";

	$optionList = "[";
	$conn->set_charset('utf8mb4');
    $result = $conn->query($sql);
	
	if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
           $optionList = $optionList.'{"optionid":'.$row["id"].',"name":"'.$row["reason"].'"},'; 
        }
		$optionList = substr($optionList,0,-1);
		$optionList = $optionList."]";
        $conn->close();
    }
	logr("getReasonOptions","info","options: ".$optionList);
	return $optionList;
}


function getNameSuffix($name){
	$vowels = 'aıouAIOUeiöüEİÖÜ';
	
	if(strpos($vowels,substr($name,-1,1)) !== false){
		if(strpos($vowels,substr($name,-1,1))<9){
			return $name . "'ya";
		} else {
			return $name . "'ye";
		}
	}else if(strpos($vowels,substr($name,-2,1)) !== false){
		if(strpos($vowels,substr($name,-2,1))<9){
			return $name . "'a";
		} else {
			return $name . "'e";
		}
	}

	
	return $name;
}


function hasWaitingTransaction($sender, $minute){
    $conn = getConnection();
    $sql = "select count(*) co from " . $GLOBALS['dbname'] . ".financial_transaction where sender = '".$sender."' 
        and is_active = 1 and result = '120' and createDate > now() - interval ".$minute." minute;";
	$result = $conn->query($sql);
	
	if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $count = number_format($row["co"]);
        }
        $conn->close();
        return $count > 0;
    }

    return false;
}

function transactionCount(){
    $conn = getConnection();
    $sql = "select count(*) co from " . $GLOBALS['dbname'] . ".financial_transaction where is_active = 1 and result = '120';";
	$result = $conn->query($sql);
	
	if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
            $count = number_format($row["co"]);
        }
        $conn->close();
        return $count;
    }

    return 0;
}

function getTopReasons(){
    $conn = getConnection();
    $sql = "SELECT r.reason, count(1) co FROM ".$GLOBALS['dbname'].".financial_transaction ft, ".$GLOBALS['dbname'].".reason r WHERE ft.is_active = 1 and ft.result = '120' and ft.reasonID = r.id group by r.reason order by co desc;";
	$reasonList = "Adet - Sebep\n";
	$conn->set_charset('utf8mb4');
    $result = $conn->query($sql);
	
	if ($result->num_rows > 0) {
        // output data of each row
        while ($row = $result->fetch_assoc()) {
           $reasonList = $reasonList."\n".$row["co"]." - ".$row["reason"]; 
        }
        $conn->close();
        return $reasonList;    
    }
	return $reasonList;

}
