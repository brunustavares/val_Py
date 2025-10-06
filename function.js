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
 * @copyright  Copyright (C) 2019-2025 Bruno Tavares
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

let report_log;
let report;

function open_report() {
    report = window.open('', "Popup", "width=800, height=600");
    let newTab = document.implementation.createHTMLDocument('val.Py report');
    let newDiv = newTab.createElement('div');
    let DivTop = `<!DOCTYPE html>
                  <meta name='viewport' content='width=device-width, initial-scale=1'/>
                  <html>
                      <head>
                          <link rel='stylesheet' href='../blocks/val_py/style.css'/>
                      </head>
                      <body>
                          <pre>`;
    let DivBottom = `     </pre>
                      </body>
                  </html>`;

    newDiv.id = "report_log";
    newDiv.textContent = report_log;
    newTab.body.appendChild(newDiv);
    report.document.write(DivTop + newTab.documentElement.innerHTML + DivBottom);

    highlightWord('OK', 'OK', 'OK', newDiv.id);
    highlightWord('erro', 'erro', 'erro', newDiv.id);
    highlightWord('naoOUoculto', 'nao/oculto', 'erro', newDiv.id);
    highlightWord('ERR_grave', 'ERRO', 'erro', newDiv.id);
    highlightWord('NO_grave', 'NAO', 'erro', newDiv.id);
    highlightWord('alerta', 'alerta', 'alerta', newDiv.id);
    highlightWord('naoUtilizado', 'nao utilizado', 'nao_utilizado', newDiv.id);
    
}

function highlightWord(oldWord, newWord, className, divID) {
    const report_div = report.document.getElementById(divID);
    const regex = new RegExp(`\\b${oldWord}\\b`, 'gi');
    
    report_div.innerHTML = report_div.innerHTML.replace(regex, `<span class="${className}">${newWord}</span>`);

}

function showLoaded() {
    document.getElementById("loading").style.display = 'none';
    document.getElementById("loaded").style.display = 'block';

}

function call_valPy(courseid, token) {
    $.ajax({
            url: '../blocks/val_py/val.Py',
            type: 'POST',
            data: {
                   argv1: courseid,
                   argv2: token
            },
    }).done((report) => {
                         report_log = report;

                         let string = "val.Py score:";
                         let position = report.search(string);
                         let length = string.length;
                         let score = report.substring(position + length + 1);
                         let dot = score.search(/\./);
                         let int = score.substring(0, dot);
                         let dec = score.substring(dot + 1);
                         let label = document.getElementById("valpy_score");

                         if (position >= 0) {
                             if (int < 70) {
                                 label.style.color = "darkred";
                             } else if (int < 100) {
                                 label.style.color = "orange";
                             } else {
                                 label.style.color = "green";
                             }
   
                             label.innerHTML = int + ".<br>" + dec;
                             label.setAttribute('title', "abrir relatório");
                             label.addEventListener('click', open_report);

                         } else {
                             label.style.color = "darkred";
                             label.innerHTML = "er<br>ro";
                             label.setAttribute('title', "enviar informação de erro");
                             label.addEventListener('click', function() {
                                 window.location.href = 'mailto:bruno.tavares@uab.pt?subject=erro val.Py | ID#' . concat(courseid) .
                                                                            concat('&body=https://elearning.uab.pt/course/view.php?id=' . concat(courseid));
                             });
                         }

                         showLoaded();

    });

}
