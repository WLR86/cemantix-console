<?php

class Cemantix {
    static $cemantix='https://cemantix.herokuapp.com/score';
    static $cache_path="/tmp/";
    static $cache=[];
    static $s_cache=[];
    static $limit=20;

    private static function postWord($word=null) {
        $curl = curl_init();
        curl_setopt_array($curl, array(
            CURLOPT_URL => self::$cemantix,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_ENCODING => "",
            CURLOPT_MAXREDIRS => 10,
            CURLOPT_TIMEOUT => 0,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
            CURLOPT_CUSTOMREQUEST => "POST",
            CURLOPT_POSTFIELDS => "word=$word"
        ));
        $response = curl_exec($curl);
        // echo "$response\n";
        return json_decode($response);
    }

    private static function cls() {
        echo chr(27).chr(91).'H'.chr(27).chr(91).'J';
    }

    private static function loadCache($num) {
        if (($handle = fopen(self::$cache_path."cem$num.csv", "r")) !== FALSE) {
            while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
                $num = count($data);
                self::$cache[$data[0]]['word'] = $data[0];
                self::$cache[$data[0]]['score'] = $data[1];
                self::$cache[$data[0]]['percentile'] = $data[2] ?? null;
                self::$cache[$data[0]]['idx'] = count(self::$cache);
            }
            self::$s_cache = self::$cache;
            usort(self::$s_cache, ['Cemantix', 'sorter']);
            fclose($handle);
        }
    }

    private static function sorter($a, $b) {
        if ($a['percentile'] != $b['percentile'])
            return $b['percentile'] > $a['percentile'];
        return $b['score'] > $a['score'];
    }

    private static function writeCacheLine($num,$row) {
        $handle = fopen(self::$cache_path."cem$num.csv", "a");
        fputcsv($handle, $row);
        fclose($handle);
    }

    private static function init() {
        $ret = self::postWord();
        $num=$ret->num;
        echo "num:$num\n";
        self::loadCache($num);
        self::print();
    }

    /**
     * 
     * str_pad handling multibyte encoding
     * 
     * https://stackoverflow.com/a/14773638
     */
    private static function mb_str_pad($input, $pad_length, $pad_string = ' ', $pad_type = STR_PAD_RIGHT, $encoding = 'UTF-8') {
        $input_length = mb_strlen($input, $encoding);
        $pad_string_length = mb_strlen($pad_string, $encoding);

        if ($pad_length <= 0 || ($pad_length - $input_length) <= 0) {
            return $input;
        }

        $num_pad_chars = $pad_length - $input_length;

        switch ($pad_type) {
            case STR_PAD_RIGHT:
                $left_pad = 0;
                $right_pad = $num_pad_chars;
                break;

            case STR_PAD_LEFT:
                $left_pad = $num_pad_chars;
                $right_pad = 0;
                break;

            case STR_PAD_BOTH:
                $left_pad = floor($num_pad_chars / 2);
                $right_pad = $num_pad_chars - $left_pad;
                break;
        }

        $result = '';
        for ($i = 0; $i < $left_pad; ++$i) {
            $result .= mb_substr($pad_string, $i % $pad_string_length, 1, $encoding);
        }
        $result .= $input;
        for ($i = 0; $i < $right_pad; ++$i) {
            $result .= mb_substr($pad_string, $i % $pad_string_length, 1, $encoding);
        }

        return $result;
    }


    private static function print($word=null) {
        self::cls();
        if ($word!=null) {
            if (isset(self::$cache[$word])) {
                echo sprintf('%4s', self::$cache[$word]['idx']) .self::mb_str_pad($word, 20, ' ', STR_PAD_LEFT)  . 
                sprintf(" : %6.2f%% / %4s\n\n", self::$cache[$word]['score'] * 100, 
                self::$cache[$word]['percentile'] > 0 ? self::$cache[$word]['percentile'] : '');
            } else {
                echo "$word\n\n";
            }
        }
        usort(self::$s_cache, ['Cemantix', 'sorter']);
        for ($hit = $i = 0 ; $i < self::$limit; $i++) {
            if (!isset(self::$s_cache[$i]))
                break ;
            $t=self::$s_cache[$i];
            if ($word == $t['word']) { echo "\033[1m"; $hit=1;}
            echo sprintf('%4s', $t['idx']) .self::mb_str_pad($t['word'], 20, ' ', STR_PAD_LEFT)  . sprintf(" : %6.2f%% / %4s\n", $t['score'] * 100, $t['percentile'] > 0 ? $t['percentile'] : '');
            if ($word == $t['word']) echo "\033[0m";
        }
        if ($hit==0 && $word != null && isset(self::$cache[$word])) {
            $t=self::$cache[$word];
            echo sprintf('%4s', $t['idx']) ."\033[1m".self::mb_str_pad($t['word'], 20, ' ', STR_PAD_LEFT)  . 
            sprintf(" : %6.2f%% / %4s\n", $t['score'] * 100, 
                $t['percentile'] > 0 ? $t['percentile'] : '') . "\033[0m";
        }
    }

    public static function start() {
        self::init();
        while(1){
            $word = readline('word : ');
            if (isset(self::$cache[$word])) {
                self::print($word);
            } else {
                $ret = self::postWord($word);
                if (isset($ret->score)) {
                    self::$cache[$word]['word']=$word;
                    self::$cache[$word]['score']=$ret->score;
                    self::$cache[$word]['percentile']=$ret->percentile ?? 0;
                    self::$cache[$word]['idx'] = count(self::$cache);
                    self::$s_cache[]=self::$cache[$word];
                    self::print($word);
                    self::writeCacheLine($ret->num,[$word,$ret->score,($ret->percentile ?? 0)]);
                } else {
                    self::print($ret->error);
                }
            }
        }
    }

}

Cemantix::start();