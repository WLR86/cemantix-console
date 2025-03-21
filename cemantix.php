<?php

error_reporting(0);

class Cemantix
{
    public static $cemantix   = 'https://cemantix.certitudes.org' ;
    public static $cache_path = '~/.cemantix/';
    public static $cache      = [] ;
    public static $s_cache    = [] ;
    public static $limit      = 20 ;
    public static $padding    = 20 ;
    public static $solvers    = null ;
    public static $startDate  = "" ;
    public static $lastResp   = "" ;
    public static $num        = 0 ;
    public static $commands   = ['/help','/quit','/exit','/restart','/nearby','/history','load'];

    private static function returnStartDate()
    {
        return self::$startDate ;
    }

    private static function cfgCurl($curl)
    {
        curl_setopt_array($curl, array(
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_ENCODING       => "",
            CURLOPT_MAXREDIRS      => 10,
            CURLOPT_TIMEOUT        => 3,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HTTP_VERSION   => CURL_HTTP_VERSION_1_1,
        ));

    }

    private static function get($item)
    {
        $curl = curl_init();
        self::cfgCurl($curl);
        curl_setopt_array($curl, array(
            CURLOPT_URL            => self::$cemantix."/".$item."?n=".self::$num,
            CURLOPT_CUSTOMREQUEST  => "GET",
        ));
        $response = curl_exec($curl);
        $ret = new stdClass();
        if (curl_errno($curl) > 0) {
            error_log("curl_error:".curl_error($curl));
            $ret->error = curl_error($curl);
        } else {
            $ret = json_decode($response);
        }
        curl_close($curl);
        return $ret ;
    }

    private static function postWord($action, $word = null)
    {
        $curl = curl_init();
        self::cfgCurl($curl);
        curl_setopt_array($curl, array(
            CURLOPT_URL            => self::$cemantix."/".$action."?n=".self::$num	,
            CURLOPT_CUSTOMREQUEST  => "POST",
            CURLOPT_HTTPHEADER     => [
                'Origin: '.self::$cemantix
            ],
            CURLOPT_POSTFIELDS     => "word=$word"
        ));
        $response = curl_exec($curl);
        $ret = new stdClass();
        if (curl_errno($curl) > 0) {
            error_log("curl_error:".curl_error($curl));
            $ret->error = "($word) ".curl_error($curl);
        } else {
            $ret = json_decode($response);
        }
        self::$lastResp = $ret ;

        // variables have been renamed
        $ret->score      = $ret->s ;
        $ret->percentile = $ret->p ;
        $ret->solvers    = $ret->v ;
        $ret->error      = $ret->e ;

        if (isset($ret->solvers)) {
            self::$solvers = $ret->solvers;
        }
        curl_close($curl);
        return $ret;
    }

    private static function cls()
    {
        echo chr(27).chr(91).'H'.
             chr(27).chr(91).'J';
    }

    private static function loadCache($num)
    {
        self::$cache_path = str_replace(
            '~',
            getenv('HOME'),
            self::$cache_path
        );
        if (!is_dir(self::$cache_path)) {
            mkdir(self::$cache_path, 0755, true);
        }
        $filename = self::$cache_path."cem".$num.".csv" ;
        if (($handle = fopen($filename, "r")) !== false) {
            self::$cache   = [];
            while (($data = fgetcsv($handle, 1000, ",")) !== false) {
                self::$cache[$data[0]]['word']       = $data[0];
                self::$cache[$data[0]]['score']      = $data[1];
                self::$cache[$data[0]]['percentile'] = $data[2] ?? null;
                self::$cache[$data[0]]['idx']        = count(self::$cache);
            }
            self::$s_cache = self::$cache;
            usort(self::$s_cache, ['Cemantix', 'sorter']);
            fclose($handle);
        } else {
            error_log("File $filename not found") ;
        }
    }

    private static function sorter($a, $b)
    {
        if ($a['percentile'] != $b['percentile']) {
            return $b['percentile'] > $a['percentile'];
        }
        return $b['score'] > $a['score'];
    }

    private static function writeCacheLine($row)
    {
        $handle = fopen(self::$cache_path."cem".self::$num.".csv", "a");
        fputcsv($handle, $row);
        fclose($handle);
    }

    private static function completeCmd($str)
    {
        return self::$commands ;
    }

    private static function loadFile($num)
    {
        if ($num == 'today') {
            $num = self::getNum() ;
        }
        self::$num = $num ;
        self::loadCache($num);
        self::print();
    }

    private static function init()
    {
        self::$startDate = date('Ymd');
        self::$num = self::getNum();
        self::loadCache(self::$num);
        self::print();
    }

    private static function getNum()
    {
        $origin = new DateTime("2022-03-03");

        // Obtenir la date du jour
        $today = new DateTime();

        // Calcul du numéro du jour
        $interval = $origin->diff($today);
        $num = $interval->days + 1; // +1 car le 03/03/2022 est le jour 1

        return $num ;
    }
    /**
     *
     * str_pad handling multibyte encoding
     *
     * https://stackoverflow.com/a/14773638
     */
    private static function mb_str_pad($input, $pad_length, $pad_string = ' ', $pad_type = STR_PAD_RIGHT, $encoding = 'UTF-8')
    {
        $input_length = mb_strlen($input, $encoding);
        $pad_string_length = mb_strlen($pad_string, $encoding);

        if ($pad_length <= 0 || ($pad_length - $input_length) <= 0) {
            return $input;
        }

        $num_pad_chars = $pad_length - $input_length;

        switch ($pad_type) {
            case STR_PAD_RIGHT:
                $left_pad  = 0;
                $right_pad = $num_pad_chars;
                break;

            case STR_PAD_LEFT:
                $left_pad  = $num_pad_chars;
                $right_pad = 0;
                break;

            case STR_PAD_BOTH:
                $left_pad  = floor($num_pad_chars / 2);
                $right_pad = $num_pad_chars - $left_pad;
                break;
        }

        $result = '';
        for ($i = 0; $i < $left_pad; ++$i) {
            $result .= mb_substr(
                $pad_string,
                $i % $pad_string_length,
                1,
                $encoding
            );
        }
        $result .= $input;
        for ($i = 0; $i < $right_pad; ++$i) {
            $result .= mb_substr(
                $pad_string,
                $i % $pad_string_length,
                1,
                $encoding
            );
        }

        return $result;
    }

    private static function print_row($row, $s_idx = null, $bold = false, $solvers = null)
    {
        $style = '0';
        $color = '0';
        $temperature = $row['percentile']  ;
        if ($temperature == 1000) {
            $icon = "🥳";
        }
        if ($temperature <  1000) {
            $icon = "😱";
        }
        if ($temperature <  999) {
            $icon = "🔥";
        }
        if ($temperature <  990) {
            $icon = "🥵";
        }
        if ($temperature <  900) {
            $icon = "😎";
        }
        if ($temperature <  1) {
            $icon = "🥶";
        }
        if ($temperature <  -100) {
            $icon = "🧊";
        }
        if ($bold) {
            $style = '1';
        }
        if ($row['percentile'] > 990) {
            $color = '31';
        } elseif ($row['percentile'] > 900) {
            $color = '33';
        } elseif (!empty($row['percentile'])) {
            $color = '93';
        }
        echo "\e[$style;${color}m";
        echo sprintf(
            "\e[$style;${color}m*\e[0m\e[${style}m %4s",
            $row['idx']
        ) .self::mb_str_pad(
            $row['word'],
            self::$padding,
            ' ',
            STR_PAD_LEFT
        )
            .
            sprintf(
                " : %6.2f°C $icon \e[$style;${color}m%4s\e[0m\e[${style}m",
                $row['score'] * 1E2,
                $row['percentile'] > 0 ? $row['percentile'] : ''
            );
        if (!is_null($s_idx)) {
            printf(
                " \e[$style;${color}m%20s\e[0m\e[${style}m%4s/%-3s ",
                self::mb_str_pad(
                    str_repeat('◼', $row['percentile'] * 2E-2),
                    self::$padding,
                    ' ',
                    STR_PAD_RIGHT
                ),
                $s_idx + 1,
                count(self::$s_cache)
            );
        } elseif (!is_null($solvers)) {
            printf(" solvers : %s", (int) $solvers);
        }
        echo "\e[0m\n";
    }

    private static function print($word = null)
    {
        self::getScreenSize();
        self::cls();
        if ($word != null) {
            if (isset(self::$cache[$word])) {
                self::print_row(
                    self::$cache[$word],
                    null,
                    false,
                    self::$solvers
                );
                echo "\n";
            } else {
                echo strip_tags("$word\n\n");
            }
        }
        usort(self::$s_cache, ['Cemantix', 'sorter']);
        foreach (self::$s_cache as $i => $t) {
            if ($i < self::$limit) {
                self::print_row($t, $i, $word == $t['word']);
            } elseif ($word == $t['word']) {
                self::print_row($t, $i, true);
            }
        }
    }

    private static function history()
    {
        $ret = self::get('history');
        self::cls();
        echo "History:\n";
        for ($i = 0; $i < self::$limit + 2; $i++) {
            $N = $ret[$i][0];
            $S = $ret[$i][1];
            $W = $ret[$i][2];
            $line = 0 + shell_exec(
                "grep 1,1000 ".self::$cache_path.
                "cem".$N.".csv -n 2>/dev/null".
                " | cut -d: -f1"
            );
            $found = ($line > 0) ? "✅" : "❌" ;
            $color = ($line > 0) ? "97" : "90" ;
            $line  = ($line == 0) ? "  " : $line ;
            echo sprintf(
                "\e[0;${color}m*\t%4u\t%7u\t".
                self::mb_str_pad($W, 20, ' ', STR_PAD_LEFT).
                "\t%5s ".$found."\t\e[0m\n",
                $N,
                $S,
                $line
            ) ;
        }
    }

    private static function nearby()
    {
        if (self::$s_cache[0]['percentile'] == 1000) {
            $ret = self::postWord('nearby', self::$s_cache[0]['word']);
            $ret = json_decode(json_encode($ret), true);
            uasort($ret, function ($a, $b) {
                return $b[0] <=> $a[0]; // Tri décroissant sur le premier élément
            });
            self::cls();
            echo "Nearby:\n";
            $i = 0 ;
            foreach ($ret as $item => $values) {
                $i++ ;

                if ($i < (self::$limit + 3)) {
                    $t['idx']        = $i;
                    $t['word']       = $item;
                    $t['score']      = $values[1] / 100;
                    $t['percentile'] = $values[0];
                    self::print_row($t);
                }
            }
        } else {
            self::print("Cheater :)");
        }
    }

    private static function help()
    {
        self::cls();
        echo "
/help		You are here

/history	Prints a list of previous words.
		Depending on your terminal's size, the
		number of displayed results may vary.
/load Num	Load the game corresponding to the given
		number. To get back to current game, you can
		give its number or use «today» as a value
/nearby		Prints a list of the highest ranked words
		for the current day, in descending order of
		relevance.  You obviously need to find the word
		for this to work.  Depending on your terminal's
		size, the number of displayed results may vary.

/restart	Resets the current game, so you can start
		from scratch. (A backup is created, though)

/reset		Alias for /restart

/quit		Self explanatory

(Press Enter to return to the game)
		";
    }

    private static function debug()
    {
        echo self::$lastResp;
    }

    private static function stop()
    {
        exit ;
    }

    private static function clean()
    {
        $num = self::get('stats')->num ;
        self::$num = $num ;
        $file = self::$cache_path."cem".$num.".csv" ;
        rename(
            $file,
            str_replace('csv', 'bak.csv', $file)
        )	;
        self::$cache   = [];
        self::$s_cache = [];
        self::start();
    }

    private static function cmd($cmd, $params = null)
    {
        switch ($cmd) {
            case 'nearby':
                self::nearby();
                break;
            case 'history':
                self::history();
                break;
            case 'reset':
            case 'restart':
                self::clean();
                break;
            case 'load':
                self::loadFile($params);
                break;
            case 'exit':
            case 'quit':
                self::stop();
                break;
            case 'help':
            case 'h':
            case '?':
                self::help();
                break;
            case 'debug':
                self::debug();
                break;
            case 'exec':
                eval($params.";");
                break;
            default:
                error_log("Unknown cmd <$cmd>");
        }
    }

    private static function getScreenSize()
    {
        preg_match_all(
            "/rows.([0-9]+);.columns.([0-9]+);/",
            strtolower(exec('stty -a |grep columns')),
            $output
        );
        if (sizeof($output) == 3) {
            self::$limit = $output[1][0] - 5;
        }
    }

    public static function start()
    {
        self::getScreenSize();
        self::init();
        readline_completion_function(['self','completeCmd']);
        while (1) {
            echo "\n";
            $word = trim(readline('> '), ' ');
            $word = preg_replace("/[^a-zA-Z\-\/\p{L}\s]`u/", "", $word);
            readline_add_history($word);
            if (preg_match('#^\/([a-z]+).*#', $word, $cmd)) {
                $params = str_replace('/'.$cmd[1].' ', '', $cmd[0]);
                self::cmd($cmd[1], $params);
            } elseif (isset(self::$cache[$word])) {
                self::print($word);
            } else {
                $ret = self::postWord('score', $word);
                // Check current date
                if (date('Ymd') > self::returnStartDate()) {
                    self::clean();
                }
                if (isset($ret->score)) {
                    self::$cache[$word]['word']       = $word;
                    self::$cache[$word]['score']      = $ret->score;
                    self::$cache[$word]['percentile'] = $ret->percentile ?? 0;
                    self::$cache[$word]['idx']        = count(self::$cache);
                    self::$s_cache[]                  = self::$cache[$word];
                    self::print($word);
                    self::writeCacheLine(
                        [$word,$ret->score,($ret->percentile ?? 0)]
                    );
                } else {
                    self::print($ret->error);
                }
            }
        }
    }
}

Cemantix::start();
