<?php
	try {
		$db = new PDO("mysql:host=172.17.0.2;
				port=3306;dbname=demo","root","admin");
		 echo "=================   La connexion a bien commence   ================="."<br>";
	}catch(PDOException  $e ) {
		echo "Error: " . $e;
	}

	$sql = "SELECT * FROM a";
	$requete = $db->query($sql);
	foreach($requete as $row) {
		echo  $row->testCol1 . "Ca fonctionne !!";
	}
