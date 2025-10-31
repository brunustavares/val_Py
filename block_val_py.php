<?php
/**
 * val.Py
 * Python bot, combined with a Moodle block, to support courses’ structure validation,
 * using various approaches, between web scraping and direct access to the database.
 * (developed for UAb - Universidade Aberta)
 *
 * @category   moodle_block
 * @package    block_val_py
 * @author     Bruno Tavares <brunustavares@gmail.com>
 * @link       https://www.linkedin.com/in/brunomastavares/
 * @copyright  Copyright (C) 2023-present Bruno Tavares
 * @license    GNU General Public License v3 or later
 *             https://www.gnu.org/licenses/gpl-3.0.html
 * @version    2025071702
 * @date       2023-12-11
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

class block_val_py extends block_base
{

    public $blockname = null;
    protected $contentgenerated = false;
    protected $docked = null;

    /**
     * Initializes class member variables.
     */
    public function init()
    {
        // Needed by Moodle to differentiate between blocks.
        $this->blockname = get_class($this);
        $this->title = '';
        $this->content_type = BLOCK_TYPE_TEXT;

    }

    /**
     * Allows configuration of the block.
     *
     * @return bool True if the configuration is allowed.
     */
    function instance_allow_config()
    {
        return true;
        
    }

    /**
     * Enables global configuration of the block in settings.php.
     *
     * @return bool True if the global configuration is enabled.
     */
    public function has_config()
    {
        return true;

    }

    /**
     * Sets the applicable formats for the block.
     *
     * @return string[] Array of pages and permissions.
     */
    public function applicable_formats()
    {
        return array('all' => true);

    }

     /**
     * Allows multiple instances.
     *
     * @return bool True if multiple instances are allowed.
     */
    function instance_allow_multiple()
    {
        return false;
        
    }

    /**
     * Returns the block contents.
     *
     * @return stdClass The block contents.
     */
    public function get_content()
    {
        // if ($this->content !== NULL) {
        //     return $this->content;
        // }

        // if (empty($this->instance)) {
        //     $this->content = '';
        //     return $this->content;
        // }

        $this->content = new stdClass;
        // $this->content->text = '';
        // $this->content->footer = '';

        global $COURSE;

        date_default_timezone_set('Europe/Lisbon');

        //verifica se o utilizador está devidamente autenticado e detém as permissões correctas
        if (!isloggedin()
            // || !has_capability('moodle/course:create', get_context_instance(CONTEXT_SYSTEM))
            || !has_capability('moodle/site:approvecourse', get_context_instance(CONTEXT_SYSTEM))
            
        ) { //em caso negativo, não exibe qualquer conteúdo
            $this->content = '';

        } else { //em caso afirmativo, constrói a interface
            global $CFG;

            $token = hash('sha256', $CFG->passwordsaltmain . $COURSE->id);

            // copyright
            $devCR = "<div id='div_cr'>
                          <a title='desenvolvido por...'
                             href='https://www.linkedin.com/in/brunomastavares/'
                             target = '_blank'>
                              &#xA9;2024
                          </a>
                      </div>";

            $output = "<!DOCTYPE html>
                        <html>
                            <head>
                                <link rel='stylesheet' href='../blocks/val_py/style.css'/>
                                <script type='text/javascript'
                                    src='../blocks/val_py/function.js'>
                                </script>
                                <script type='text/javascript'
                                    src='https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js'>
                                </script>
                            </head>
                            <body>
                                <div id='loading'></div>
                                <div id='loaded'>
                                    <label id='valpy_score'></label>
                                </div>" .
                                $devCR . "
                                <script>
                                    call_valPy('" . $COURSE->id . "', '" . $token . "')
                                </script>
                            </body>
                        </html>";

            $this->content->text = $output;

            return $this->content;

        }

    }

}
