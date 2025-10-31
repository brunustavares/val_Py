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

defined('MOODLE_INTERNAL') || die();

if ($hassiteconfig) {
    $ADMIN->add('localplugins', new admin_category('block_val_py_settings', new lang_string('pluginname', 'block_val_py')));

    $settingspage = new admin_settingpage('manage_block_val_py', new lang_string('manage', 'block_val_py'));

    if ($ADMIN->fulltree) {
        $settings->add(new admin_setting_configtext(
                'val_py_cliusr',
                new lang_string('cliusr', 'block_val_py'),
                '',
                '',
                PARAM_TEXT));

        $settings->add(new admin_setting_configpasswordunmask(
                'val_py_clipwd',
                new lang_string('clipwd', 'block_val_py'),
                '',
                '',
                PARAM_TEXT));

    }

    $ADMIN->add('localplugins', $settingspage);

}
