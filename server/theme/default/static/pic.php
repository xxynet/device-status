<?php

$file = scandir('bg/');
$file = array_slice($file,2);
$i = rand(0,count($file)-1);
$fileres = file_get_contents("bg/".strval($file[$i]));
header('Content-type: image/jpeg');
echo $fileres;
?>