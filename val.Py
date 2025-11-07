#!/usr/local/bin/python3.9
# -*- coding: utf-8 -*-
print('Content-Type:text/html;charset=utf-8\r\n')

# pt: binários Python
# en: Python binaries
# dev  - s:/PortableApps/python/python.exe
# prod - /usr/local/bin/python3.9

#
# val.Py
# Python bot, combined with a Moodle block, to support courses’ structure validation,
# using various approaches, between web scraping and direct access to the database.
# (developed for UAb - Universidade Aberta)
#
# @category   python_script
# @package    val.Py
# @author     Bruno Tavares <brunustavares@gmail.com>
# @link       https://www.linkedin.com/in/brunomastavares/
# @copyright  Copyright (C) 2023-present Bruno Tavares
# @license    GNU General Public License v3 or later
#             https://www.gnu.org/licenses/gpl-3.0.html
# @version    2025103108
# @date       2023-12-11
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

# pt: bibliotecas utilizadas
# en: used libraries
import requests
import re
import sys
import mysql.connector
import time
import validators
import cgi
import os
import hashlib
from urllib.parse import urlparse
from requests.exceptions import SSLError
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
from tabulate import tabulate
from termcolor import colored
from datetime import datetime
from tqdm import tqdm

# pt: data padrão
# en: default data
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
EMPTY_DATE = "1970-01-01 00:00:00"

# pt: constantes
# en: constants
HTML_PARSER = 'html.parser'

ERR_MSG_IDNUM = " | erro: idnumber invalido"
ERR_MSG_GROUPS = " | alerta: modo de grupo"
ERR_MSG_MAXGRADE = " | erro: nota maxima"
ERR_MSG_GRADETYPE = " | erro: nota invalida"
ERR_MSG_CATEGORY = " | erro: categoria invalida"
ERR_MSG_OPTIONS = " | erro: opcoes desconformes"
ERR_MSG_OPTIONSNUM = " | alerta: numero de opcoes"
ERR_MSG_HIDDEN = " | alerta: oculto"
ERR_MSG_MULTI = " | alerta: multiplos"
ERR_MSG_PLAGIARISM = " | alerta: TurnitIn"
ERR_MSG_FDBKTYPE = " | alerta: tipos de feedback"
ERR_MSG_DTFILLED = " | alerta: datas preenchidas"
ERR_MSG_DTOVERLAP = " | alerta: datas sobrepostas"
ERR_MSG_DTEARLY = " | alerta: data anterior a decisao"
ERR_MSG_DTREF = " | alerta: sem data de referencia"
ERR_MSG_SUB = " | alerta: submissao"
ERR_SSL = "erro: SSL"
ERR_URL = "erro: URL invalido"
ERR_NOREPLY = "erro: sem resposta"
ERR_CONST = colored("ERR_grave", 'red')
OK_NOTITLE = "OK: sem titulo"
NO_CONST = colored("NO_grave", 'red')

# pt: obter argumentos
# en: get arguments
form = cgi.FieldStorage()
course_ID = ""

if "argv1" and "argv2" in form:
    course_ID = form['argv1'].value
    token = form['argv2'].value

elif len(sys.argv) == 2:
    course_ID = sys.argv[1]

else:
    print('acesso invalido')
    sys.exit()

if course_ID.isdigit() == False:
    print('acesso invalido')
    sys.exit()

session = requests.Session()

# pt: ficheiro config.php do Moodle
# en: Moodle's config.php file
with open(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/config.php", "r") as mdl_cfg_file:
    mdl_cfg = mdl_cfg_file.readlines()
    mdl_cfg_file.close()

    # pt: carregar variáveis a partir do ficheiro
    # en: load variables from file
    for row in mdl_cfg:
        if "//" not in row[:5]:
            if "$CFG->dbhost" in row:
                dbhost = row[row.find("'") + 1:row.rfind("'")]
            
            elif "$CFG->dbname" in row:
                dbname = row[row.find("'") + 1:row.rfind("'")]

            elif "$CFG->dbuser" in row:
                dbuser = row[row.find("'") + 1:row.rfind("'")]

            elif "$CFG->dbpass" in row:
                dbpass = row[row.find("'") + 1:row.rfind("'")]

            elif "$CFG->wwwroot" in row:
                try_URL = row[row.find("'") + 1:row.rfind("'")]

                # pt: validar estrutura do URL lido
                # en: validate URL structure
                if validators.url(try_URL):
                    wwwroot = try_URL

            elif "$CFG->passwordsaltmain" in row:
                salt = row[row.find("'") + 1:row.rfind("'")]

if len(sys.argv) == 0 and hashlib.sha256((salt + course_ID).encode()).hexdigest() != token:
    print('acesso invalido')
    sys.exit()

course_URL = wwwroot + "/course/view.php?id=" + course_ID

# pt: obter credenciais do user 'val.Py CLI'
# en: get credentials for user 'val.Py CLI'
mdl_db = mysql.connector.connect(host=dbhost, user=dbuser, password=dbpass, database=dbname)
mdl_db_cursor = mdl_db.cursor()

query = "SELECT MAX(CASE WHEN (`user`.`name` = 'val_py_cliusr') THEN `user`.`value` END) AS `username`, \
                MAX(CASE WHEN (`user`.`name` = 'val_py_clipwd') THEN `user`.`value` END) AS `password` \
         FROM (SELECT name, value \
               FROM moodle.mdl_config) AS user;"
mdl_db_cursor.execute(query)

valpy_cli = mdl_db_cursor.fetchall()
username = valpy_cli[0][0]
password = valpy_cli[0][1]

mdl_db_cursor.close()
mdl_db.close()

def auth():
    # pt: preencher formulário de autenticação
    # en: fill authentication form
    auth_url = wwwroot + '/login/index.php?username=' + username
    auth_page = session.get(auth_url)
    cookie = auth_page.cookies.get_dict()
    pattern = '<input type="hidden" name="logintoken" value="\w{32}">'
    token = re.findall(pattern, auth_page.text)
    token = re.findall("\w{32}", token[0])
    payload = {'username': username,
               'password': password,
               'anchor': '',
               'logintoken': token[0]}
    auth_page = session.post(auth_url, cookies=cookie, data=payload, allow_redirects=False)

    # pt: verificar se o URL de autenticação se mantém na PlataformAbERTA, ou se houve
        # redireccionamento para o CAS, o que significa que o login local falhou
    # en: check if the authentication URL remains in PlataformAbERTA, or if there was
        # a redirection to CAS, which means the local login failed
    if wwwroot.find(str(urlparse(auth_page.url).netloc)) == -1:
        return False

    return session

# pt: limpar caracteres especiais
# en: clean special characters
def sanitize(string):
    def replace_dirty_chars(string, dirty_chars, replacement):
        found_idxs = [idx for idx, char in enumerate(string.lower()) if char in dirty_chars]

        for idx in found_idxs:
            if string[idx].isupper():
                string = string.replace(string[idx], replacement.upper())

            else:
                string = string.replace(string[idx], replacement.lower())

        return string

    string = replace_dirty_chars(string, ['á', 'à', 'ã', 'â', 'ä', 'ª'], 'a')
    string = replace_dirty_chars(string, ['é', 'è', 'ê'], 'e')
    string = replace_dirty_chars(string, ['í', 'ï'], 'i')
    string = replace_dirty_chars(string, ['ó', 'ò', 'õ', 'ô', 'ö', 'º'], 'o')
    string = replace_dirty_chars(string, ['ú', 'ü'], 'u')
    string = replace_dirty_chars(string, ['ç'], 'c')
    string = replace_dirty_chars(string, ['ñ'], 'n')
    string = string.encode('ascii', 'ignore').decode('ascii', 'ignore')

    return string

# pt: testar se o URL dá resposta válida
# en: test if the URL returns a valid response
def validate_url(url):
    try:
        requests.get(url)

    except requests.exceptions.ConnectionError:
        return False

    return True

# pt: detectar marca de água
# en: detect watermark
def detect_watermark(img):
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        return True
    
    else:
        return False

# pt: preencher parâmetros do folio
# en: fill folio parameters
def fill_folio_cfg(row):
    folio_cfg = {}

    folio_cfg = {'id': row[0],
                 'idnumber': row[2],
                 'notatype': row[3],
                 'grademax': row[5],
                 'visible': row[7],
                 'display': row[8],
                 'feedback': row[11],
                 'plagiarism': row[12],
                 'groupmode': row[13],
                 'start': row[15],
                 'end': row[16],
                 'category': row[18],
                 'parent': row[19]
                }

    if folio_cfg['start'] is not None:
        folio_cfg['start'] = datetime.strptime(folio_cfg['start'], DATE_FORMAT)

    else:
        folio_cfg['start'] = datetime.strptime(EMPTY_DATE, DATE_FORMAT)

    if folio_cfg['end'] is not None:
        folio_cfg['end'] = datetime.strptime(folio_cfg['end'], DATE_FORMAT)
    
    else:
        folio_cfg['end'] = datetime.strptime(EMPTY_DATE, DATE_FORMAT)

    return folio_cfg

# pt: preencher parâmetros da prova final
# en: fill final test parameters
def fill_test_cfg(row):
    test_cfg = {'id': row[0],
                'idnumber': row[2],
                'notatype': row[3],
                'grademax': row[5],
                'visible': row[7],
                'display': row[8],
                'submit': row[9],
                'groupmode': row[13],
                'category': row[18]
               }
    
    return test_cfg

# pt: validar parâmetros do folio
# en: validate folio parameters
def val_folio(idnumber, folio_cfg):
    result = "sim"

    if "idnumber" not in folio_cfg or \
        folio_cfg["idnumber"] != idnumber:
        result += colored(ERR_MSG_IDNUM, 'red')

    if "grademax" not in folio_cfg or \
        folio_cfg["grademax"] > 8:
        result += colored(ERR_MSG_MAXGRADE, 'red')

    if "groupmode" not in folio_cfg or \
        folio_cfg["groupmode"] != 1:
        result += colored(ERR_MSG_GROUPS, 'red')

    if "visible" not in folio_cfg or \
        folio_cfg["visible"] != 1:
        result += colored(ERR_MSG_HIDDEN, 'red')

    if ("category" not in folio_cfg or \
        folio_cfg["category"] is None or \
        "electronica" not in sanitize(folio_cfg["category"].lower())) or \
       ("parent" not in folio_cfg or \
        folio_cfg["parent"] is None or \
        "continua" not in sanitize(folio_cfg["parent"].lower())):
        result += colored(ERR_MSG_CATEGORY, 'red')

    if "plagiarism" not in folio_cfg or \
        folio_cfg["plagiarism"] != "1":
        result += colored(ERR_MSG_PLAGIARISM, 'yellow')

    if "feedback" not in folio_cfg or \
        "comments" not in folio_cfg["feedback"].lower() or \
        "editpdf" not in folio_cfg["feedback"].lower():
        result += colored(ERR_MSG_FDBKTYPE, 'yellow')

    return result

# pt: validar parâmetros da prova final
# en: validate final test parameters
def val_test(idnumber, test_cfg, grademax, category):
    result = "sim"

    if "idnumber" not in test_cfg or \
        test_cfg["idnumber"] != idnumber:
        result += colored(ERR_MSG_IDNUM, 'red')

    if "submit" not in test_cfg or \
        test_cfg["submit"] != "0":
        result += colored(ERR_MSG_SUB, 'red')

    if "notatype" not in test_cfg or \
        test_cfg["notatype"].lower() != "nota":
        result += colored(ERR_MSG_GRADETYPE, 'red')

    if "grademax" not in test_cfg or \
        test_cfg["grademax"] > grademax:
        result += colored(ERR_MSG_MAXGRADE, 'red')

    if "groupmode" not in test_cfg or \
        test_cfg["groupmode"] != 1:
        result += colored(ERR_MSG_GROUPS, 'red')

    if "visible" not in test_cfg or \
        test_cfg["visible"] != 1:
        result += colored(ERR_MSG_HIDDEN, 'red')

    if (category is None or \
        "category" not in test_cfg or \
        test_cfg["category"] is None or \
        category.lower() not in test_cfg["category"].lower()):
        result += colored(ERR_MSG_CATEGORY, 'red')

    return result

def main():
    T_items = 0
    T_pnlt = 0
    valPy_score = 0

    # pt: testar se o URL dá resposta válida
    # en: test if the URL returns a valid response
    if not validate_url(wwwroot):
        print(colored("URL invalido", 'red'))
        sys.exit()

    # pt: obter autenticação
    # en: get authentication
    if not auth():
        print(colored("Login invalido", 'red'))
        sys.exit()

    page2validate = session.get(course_URL)

    # pt: verificar se a UC existe
    # en: check if the course exists
    if page2validate.status_code != 200:
        print(colored("UC nao encontrada", 'yellow'))
        sys.exit()

    # pt: abrir ligação à BD
    # en: open connection to DB
    mdl_db = mysql.connector.connect(host=dbhost, user=username, password=password, database=dbname)
    mdl_db_cursor = mdl_db.cursor()

    # pt: identificar tipologia da UC
    # en: identify course typology
    query = "SELECT idnumber, summary \
             FROM moodle.mdl_course \
             WHERE id = '" + course_ID + "';"
    mdl_db_cursor.execute(query)
    myresult = mdl_db_cursor.fetchone()
    
    if int(myresult[0][1]) == 1 or 'Unidade curricular do 1º ciclo' in myresult[1]:
        UC_type = 1

    elif int(myresult[0][1]) > 1 or 'Unidade curricular do 2º / 3º ciclo' in myresult[1]:
        UC_type = 2

    # pt: validar todos os recursos
    # en: validate all resources

    # pt: ler página da UC
    # pt: read course page
    page = BeautifulSoup(page2validate.content, HTML_PARSER)

    # pt: isolar bloco Campus Virtual
    # en: isolate Campus Virtual block
    blockCV = page.find_all('section', attrs={'data-block': 'lanca_pauta'})

    # pt: isolar PUC/CdA
    # en: isolate course plan
    if UC_type == 1:
        PUC_obj = page.find_all(lambda tag: tag.has_attr('data-activityname') and
                               (('plano da unidade curricular' in (tag['data-activityname']).lower()) or 
                                ('curricular unit plan' in (tag['data-activityname']).lower()) or 
                                ('PUC' in (tag['data-activityname']))))
        
        if (len(PUC_obj)) > 0:
            try:
                PUC_obj_URL = PUC_obj[0].find('a')['href']

            except Exception:
                PUC_obj_URL = None

        else:
            PUC_obj_URL = None

    elif UC_type == 2:
        CdA_obj = page.find_all(lambda tag: tag.has_attr('data-activityname') and
                               (('contrato de aprendizagem' in (tag['data-activityname']).lower()) or 
                                ('learning contract' in (tag['data-activityname']).lower())))
        
        if (len(CdA_obj)) > 0:
            try:
                CdA_obj_URL = CdA_obj[0].find('a')['href']

            except Exception:
                CdA_obj_URL = None

        else:
            CdA_obj_URL = None

    # pt: isolar itens da UC
    # en: isolate course items
    items = page.find_all('span', attrs={'class': 'instancename'})

    # pt: inicializar variáveis de controlo
    # en: initialize control variables
    bloco_CampusVirtual = colored("naoOUoculto", 'red')
    forum_Noticias = NO_CONST
    PUC = NO_CONST
    CdA = NO_CONST
    decisao = NO_CONST
    decisao_end = EMPTY_DATE
    efolio_A = NO_CONST
    efolio_B = NO_CONST
    efolio_C = NO_CONST
    pfolio = NO_CONST
    exame = NO_CONST
    formula = ERR_CONST
    somatorio = ERR_CONST
    # topico_WISEflow = NO_CONST
    flow_type = NO_CONST

    UC = colored("\n" + sanitize(page.title.text), 'green')

    if UC_type == 1:
        UC += " (1º ciclo)"

    elif UC_type == 2:
        UC += " (2º / 3º ciclo)"

    # pt: validar configurações gerais da UC
    # en: validate general course settings
    T_items += 1

    query = "SELECT crs.fullname, \
                    crs.shortname, \
                    crs.idnumber, \
                    crs.visible, \
                    crs.format, \
                    round(crs.maxbytes/1048576, 2), \
                    crs.groupmode, \
                    REPLACE(GROUP_CONCAT(crs_group.name SEPARATOR ', '), ', ', ',\n'), \
                    REPLACE(GROUP_CONCAT(rl.name SEPARATOR ', '), ', ', ',\n'), \
                    crs.lang, \
                    from_unixtime(crs.startdate), \
                    from_unixtime(crs.enddate), \
                    crs.enablecompletion \
             FROM moodle.mdl_course crs \
                 LEFT JOIN moodle.mdl_groups crs_group ON crs_group.courseid = crs.id \
                 LEFT JOIN moodle.mdl_context ctx ON ctx.instanceid = crs.id \
                 LEFT JOIN moodle.mdl_role_names rl ON rl.contextid = ctx.id \
             WHERE ctx.contextlevel = 50 \
                 AND crs.id = '" + course_ID + "';"
    mdl_db_cursor.execute(query)
    myresult = mdl_db_cursor.fetchall()

    if myresult[0][1] != myresult[0][2]:
        UC += colored(" | alerta: shortname/idnumber", 'yellow')
        T_pnlt = 1

    if myresult[0][3] != 0:
        UC += colored(" | alerta: visivel", 'yellow')
        T_pnlt = 1

    if myresult[0][6] != 0:
        UC += colored(ERR_MSG_GROUPS, 'yellow')
        T_pnlt = 1

    headers = ["\nnome",
               "\ncodigo",
               "\nidnumber",
               "\nvisivel",
               "\nformato",
               "tamanho dos\nficheiros (Mb)",
               "\nmodo de grupo",
               "grupos /\nagrupamentos",
               "papeis\npersonalizados",
               "\nlingua",
               "\ninicio",
               "\nfim",
               "conclusao de\nactividades\nactivada"]
    UC += "\n" + tabulate(myresult, headers, tablefmt="pretty", stralign="center") + "\n"

    if T_pnlt == 0:
        valPy_score += 1
    
    else:
        T_pnlt = 0

    print(sanitize(UC))

    time.sleep(1)

    # pt: validar perfis atribuidos
    # en: validate assigned profiles
    T_items += 1

    profiles = "perfis atribuidos"

    query = "SELECT CONCAT(teach.firstname, ' ', teach.lastname), \
                    teach.email, \
                    teach.username, \
                    rl.name, \
                    IF(grps_mbrs.userid IS NOT NULL, \
                    GROUP_CONCAT(grps.name SEPARATOR ', '), \
                    NULL) \
             FROM mdl_course crs \
                 INNER JOIN mdl_context ctx ON (ctx.instanceid = crs.id \
                                                AND ctx.contextlevel = 50) \
                 INNER JOIN mdl_role_assignments rl_asg ON rl_asg.contextid = ctx.id \
                 INNER JOIN mdl_role rl ON rl.id = rl_asg.roleid \
                 INNER JOIN mdl_user teach ON teach.id = rl_asg.userid \
                 LEFT JOIN moodle.mdl_groups grps ON grps.courseid = crs.id \
                 LEFT JOIN moodle.mdl_groups_members grps_mbrs ON (grps_mbrs.groupid = grps.id \
                                                                   AND grps_mbrs.userid = teach.id) \
             WHERE crs.id = '" + course_ID + "' \
                 AND (rl.shortname NOT LIKE '%student%' \
                     AND rl.shortname NOT LIKE '%xp%' \
                     AND rl.shortname NOT LIKE '%ampv%') \
             GROUP BY teach.id, rl.id, grps_mbrs.userid \
             ORDER BY teach.username, rl.name;"
    mdl_db_cursor.execute(query)
    myresult = mdl_db_cursor.fetchall()

    for row in myresult:
        if row[4] is not None and ERR_MSG_GROUPS not in profiles:
            profiles += colored(ERR_MSG_GROUPS, 'yellow')
            T_pnlt = 1

    headers = ["\nnome",
               "\nemail",
               "\nusername",
               "\nperfil",
               "\ngrupos"]
    profiles += "\n" + tabulate(myresult, headers, tablefmt="pretty", stralign="left") + "\n"

    if T_pnlt == 0:
        valPy_score += 1

    else:
        T_pnlt = 0

    print(sanitize(profiles))

    time.sleep(1)

    # pt: validar bloco Campus Virtual
    # en: validate Campus Virtual block
    T_items += 1

    if len(blockCV) > 0:
        bloco_CampusVirtual = "sim"

        if len(blockCV) > 1:
            bloco_CampusVirtual += colored(ERR_MSG_MULTI, 'yellow')
        
        for b in blockCV:
            if "erro:" in b.text.lower():
                bloco_CampusVirtual = ERR_CONST

    if bloco_CampusVirtual == "sim":
        bloco_CampusVirtual = colored("OK", 'green')
        valPy_score += 1

    bloco_CampusVirtual = "bloco Campus Virtual: " + bloco_CampusVirtual

    print(sanitize(bloco_CampusVirtual))

    time.sleep(1)

    if UC_type == 1:
        # pt: validar PUC
        # en: validate course plan
        T_items += 1

        for item in items:
            if (PUC_obj_URL is not None and
               ((("plano da unidade curricular" in item.text.lower()) or
                 ("curricular unit plan" in item.text.lower()) or
                 ("PUC" in item.text)) and
                ("livro" in item.text.lower() or
                 "book" in item.text.lower()))):
                PUC2validate = session.get(PUC_obj_URL)
                PUC_content = BeautifulSoup(PUC2validate.content, HTML_PARSER)
                try:
                    PUC_UC = PUC_content.find('a', attrs={'title': '1. A Unidade Curricular'})['href']
                
                except Exception:
                    PUC_UC = None

                if PUC_UC is not None:
                    PUC = "sim"
                    PUC_UC_URL = PUC_obj_URL + PUC_UC[PUC_UC.find("&"):]
                    PUC2validate = session.get(PUC_UC_URL)
                    PUC_content = BeautifulSoup(PUC2validate.content, HTML_PARSER)
                    PUC_UC_main = PUC_content.find('div', attrs={'role': 'main'})

                    if "[...Incluir Sinopse da Unidade Curricular ...]" in PUC_UC_main.text:
                        PUC += colored(" | alerta: por preencher", 'yellow')

                    elif " erro" in PUC_UC_main.text:
                        PUC += colored(" | erro: PUC danificado", 'red')

                    break

        if PUC == "sim":
            PUC = colored("OK", 'green')
            valPy_score += 1

        PUC = "PUC: " + PUC

        print(sanitize(PUC))

    elif UC_type == 2:
        # pt: validar CdA
        # en: validate course plan
        T_items += 1

        for item in items:
            if (CdA_obj_URL is not None and
               ((("contrato de aprendizagem" in item.text.lower()) or
                 ("learning contract" in item.text.lower())) and
                ("livro" in item.text.lower() or
                "book" in item.text.lower()))):
                CdA = "sim"
                CdA2validate = session.get(CdA_obj_URL)
                CdA_content = BeautifulSoup(CdA2validate.content, HTML_PARSER)
                CdA_UC_main = CdA_content.find('div', attrs={'role': 'main'})

                if " erro" in CdA_UC_main.text:
                    CdA += colored(" | erro: CdA danificado", 'red')

                break

        if CdA == "sim":
            CdA = colored("OK", 'green')
            valPy_score += 1

        CdA = "CdA: " + CdA

        print(sanitize(CdA))

    time.sleep(1)

    # pt: validar fórum Notícias
    # en: validate News forum
    T_items += 1

    for item in items:
        if (("noticias" in sanitize(item.text.lower())) or 
            ("news" in item.text.lower())) and \
            "forum" in sanitize(item.text.lower()):
            forum_Noticias = "sim"

            query = "SELECT type, \
                            name, \
                            intro, \
                            idnumber, \
                            visible, \
                            groupmode \
                     FROM moodle.mdl_forum newsF \
                         INNER JOIN moodle.mdl_course_modules crsMod ON (crsMod.course = newsF.course AND crsMod.instance = newsF.id) \
                     WHERE newsF.course = '" + course_ID + "' \
                         AND (LOWER(newsF.name) LIKE '%notícias%' \
                         OR LOWER(newsF.name) LIKE '%news%') \
                         AND crsMod.module = 9;"
            mdl_db_cursor.execute(query)
            myresult = mdl_db_cursor.fetchall()

            if len(myresult) == 0 or myresult[0][0] != "news":
                forum_Noticias += colored(" | alerta: inautentico", 'yellow')

            elif len(myresult) > 1:
                forum_Noticias += colored(ERR_MSG_MULTI, 'yellow')

            if myresult[0][4] != 1:
                forum_Noticias += colored(ERR_MSG_HIDDEN, 'yellow')

            if myresult[0][5] != 0:
                forum_Noticias += colored(ERR_MSG_GROUPS, 'yellow')

            break

    if forum_Noticias == "sim":
        forum_Noticias = colored("OK", 'green')
        valPy_score += 1

    forum_Noticias = "forum Noticias: " + forum_Noticias

    print(sanitize(forum_Noticias))

    time.sleep(1)

    if UC_type == 1:
        # pt: validar decisão de modo de avaliação (contínua / final)
        # en: validate decision on assessment mode (continuous / final)
        T_items += 1

        # pt: obter data de referência para o fim da decisão
        # en: get reference date for decision end
        query = "SELECT CAST(FROM_UNIXTIME(`chc`.`timeclose`) AS DATETIME) AS data_fim \
                 FROM `moodle`.`mdl_course_modules` `crs_mod` \
                     INNER JOIN `moodle`.`mdl_choice` `chc` ON `chc`.`id` = `crs_mod`.`instance` \
                     INNER JOIN `moodle`.`mdl_course` `crs` ON `crs`.`id` = `crs_mod`.`course` \
                 WHERE `crs`.`idnumber` = 'SSTE-AT' \
                     AND (`crs_mod`.`idnumber` = 'decisao_S1' \
                     OR `crs_mod`.`idnumber` = 'decisao_S2') \
                 ORDER BY data_fim ASC;"
        mdl_db_cursor.execute(query)
        myresult = mdl_db_cursor.fetchall()

        if len(myresult) > 0:
            for dt in myresult:
                if dt[0] > datetime.now():
                    decisao_end = dt[0]

                    break

        for item in items:
            if "decisao sobre a avaliacao" in sanitize(item.text.lower()):
                decisao = "sim"

                query = "WITH ranked_options AS ( \
                                                 SELECT chc.id AS choice_id, \
                                                        chc.name, \
                                                        crsMod.idnumber, \
                                                        crsMod.visible, \
                                                        crsMod.groupmode, \
                                                        IF(chc.timeclose <> 0, FROM_UNIXTIME(chc.timeclose), '" + EMPTY_DATE + "') AS closedt, \
                                                        chcOpt.text AS option_text, \
                                                        ROW_NUMBER() OVER (PARTITION BY chcOpt.choiceid ORDER BY chcOpt.id) AS rownum, \
                                                        COUNT(*) OVER (PARTITION BY chcOpt.choiceid) AS total_options \
                                                 FROM moodle.mdl_choice chc \
                                                     JOIN moodle.mdl_choice_options chcOpt ON chcOpt.choiceid = chc.id \
                                                     JOIN moodle.mdl_course_modules crsMod ON (crsMod.course = chc.course AND crsMod.instance = chc.id) \
                                                 WHERE chc.course = '" + course_ID + "' \
                                                     AND chc.name LIKE '%Decisão sobre a Avaliação%' \
                                                 LIMIT 2 \
                                                ) \
                         SELECT name, \
                                idnumber, \
                                total_options AS optionT, \
                                GROUP_CONCAT(CASE WHEN rownum % 2 = 1 THEN option_text END) AS option1, \
                                GROUP_CONCAT(CASE WHEN rownum % 2 = 0 THEN option_text END) AS option2, \
                                visible, \
                                groupmode, \
                                closedt \
                         FROM ranked_options \
                         GROUP BY choice_id, name, idnumber, total_options, visible, groupmode, closedt \
                         ORDER BY name;"

                mdl_db_cursor.execute(query)
                myresult = mdl_db_cursor.fetchall()

                if myresult[0][1].lower() != "decisao":
                    decisao += colored(ERR_MSG_IDNUM, 'red')

                if myresult[0][2] != 2:
                    if myresult[0][2] > 2:
                        decisao += colored(ERR_MSG_OPTIONSNUM, 'yellow')

                    elif myresult[0][2] < 2:
                        decisao += colored(ERR_MSG_OPTIONSNUM, 'red')

                if myresult[0][3] != "Avaliação Contínua" or myresult[0][4] != "Exame":
                    decisao += colored(ERR_MSG_OPTIONS, 'red')

                if myresult[0][5] != 1:
                    decisao += colored(ERR_MSG_HIDDEN, 'yellow')

                if myresult[0][6] != 0:
                    decisao += colored(ERR_MSG_GROUPS, 'yellow')

                if str(myresult[0][7]) != EMPTY_DATE:
                    decisao += colored(ERR_MSG_DTFILLED, 'yellow')

                if decisao_end == EMPTY_DATE:
                    decisao += colored(ERR_MSG_DTREF, 'yellow')

                break

        if decisao == "sim":
            decisao = colored("OK", 'green')
            valPy_score += 1

        decisao = "decisao: " + decisao

        print(sanitize(decisao))

        time.sleep(1)

    if UC_type == 1:
        # pt: validar trabalhos
        # en: validate assignments

        # pt: identificar todos os dispositivos de avaliação e respectivas configurações
        # en: identify all assessment devices and respective configurations
        query = "SELECT grd_it.id, \
                        grd_it.itemname, \
                        grd_it.idnumber, \
                        CASE \
                            WHEN gradetype = 1 THEN 'Nota' \
                            WHEN gradetype = 2 THEN 'Escala' \
                            ELSE 'Nenhuma' \
                        END, \
                        CASE \
                            WHEN display = 1 THEN 'Real' \
                            WHEN display = 2 THEN 'Prcnt.' \
                            WHEN display = 3 THEN 'Alfa' \
                            WHEN display = 12 THEN 'Real (prcnt)' \
                            WHEN display = 13 THEN 'Real (alfa)' \
                            WHEN display = 21 THEN 'Prcnt (real)' \
                            WHEN display = 23 THEN 'Prcnt (alfa)' \
                            WHEN display = 31 THEN 'Alfa (real)' \
                            WHEN display = 32 THEN 'Alfa (prcnt)' \
                            ELSE 'predef.' \
                        END, \
                        grademax, \
                        decimals, \
                        if(grd_it.hidden = 0, 1, 0), \
                        display, \
                        if(device.nosubmissions IS NULL, 'NA', if(device.nosubmissions = 0, 1, 0)), \
                        if(device.teamsubmission IS NULL, 'NA', teamsubmission), \
                        if(asg_cfg.plugin IS NULL, 'NA', REPLACE(GROUP_CONCAT(asg_cfg.plugin SEPARATOR ', '), ', ', ',\n')), \
                        plag.value, \
                        groupmode, \
                        REPLACE(grp.name, ' ', '\n'), \
                        REPLACE(if(allowsubmissionsfromdate <> 0, from_unixtime(allowsubmissionsfromdate), NULL), ' ', '\n'), \
                        REPLACE(if(duedate <> 0, from_unixtime(duedate), NULL), ' ', '\n'), \
                        REPLACE(if(cutoffdate <> 0, from_unixtime(cutoffdate), NULL), ' ', '\n'), \
                        REPLACE(if(grd_cat.fullname <> '?', grd_cat.fullname, NULL), ' ', '\n'), \
                        REPLACE(if(grd_prt.fullname <> '?', grd_prt.fullname, NULL), ' ', '\n') \
                 FROM moodle.mdl_grade_items grd_it \
                     RIGHT JOIN ( \
                                 SELECT * \
                                 FROM ( \
                                       SELECT id, \
                                              course, \
                                              nosubmissions, \
                                              teamsubmission, \
                                              allowsubmissionsfromdate, \
                                              duedate, \
                                              cutoffdate \
                                       FROM moodle.mdl_assign \
                                       UNION ALL \
                                       SELECT id, \
                                              course, \
                                              null, \
                                              null, \
                                              timeopen, \
                                              timeclose, \
                                              null \
                                       FROM moodle.mdl_quiz \
                                      ) AS tmp \
                                 WHERE course = '" + course_ID + "' \
                                ) AS device ON (device.id = grd_it.iteminstance AND device.course = grd_it.courseid) \
                     LEFT JOIN moodle.mdl_assign_plugin_config asg_cfg ON asg_cfg.assignment = device.id \
                     LEFT JOIN moodle.mdl_course_modules crs_mod ON (crs_mod.course = device.course AND crs_mod.instance = device.id AND crs_mod.idnumber = grd_it.idnumber) \
                     LEFT JOIN moodle.mdl_groupings grp ON (grp.courseid = crs_mod.course AND grp.id = crs_mod.groupingid) \
                     LEFT JOIN moodle.mdl_grade_categories grd_cat ON grd_cat.id = grd_it.categoryid \
                     LEFT JOIN moodle.mdl_grade_categories grd_prt ON grd_prt.id = grd_cat.parent \
                     LEFT JOIN moodle.mdl_plagiarism_turnitin_config plag ON plag.cm = crs_mod.id \
                 WHERE (grd_it.itemname IS NOT NULL \
                         AND grd_it.itemname <> '') \
                     AND ((asg_cfg.subtype = 'assignfeedback' \
                             AND asg_cfg.value = '1') \
                         OR asg_cfg.subtype IS NULL) \
                     AND (plag.name = 'use_turnitin' \
                         OR plag.name IS NULL) \
                     GROUP BY grd_it.id \
                     ORDER BY itemname;"
        mdl_db_cursor.execute(query)
        myresult = mdl_db_cursor.fetchall()

        MPV = []
        PEEs = []

        for row in myresult:
            if row[2] is not None and "_global_" in row[2].lower():
                PEEs.append(row)
            
            else:
                MPV.append(row)

        headers = ["nome",
                   "idnumber",
                   "nota:\ntipo",
                   "nota:\nformato",
                   "nota:\nmax",
                   "casas\ndecimais",
                   "mostrar\nna UC",
                   "mostrar\nno CdA",
                   "submissão\nactivada",
                   "submissão\nem grupo",
                   "tipos de\nfeedback",
                   "TurnitIn",
                   "modo de\ngrupo",
                   "nome do\ngrupo",
                   "submeter\ndesde",
                   "submeter\naté",
                   "fecho",
                   "categ. CdA:\nNível 1",
                   "categ. CdA:\nNível 2"]

        efolio_A_cfg = {}
        efolio_B_cfg = {}
        efolio_C_cfg = {}
        pfolio_cfg = {}
        exame_cfg = {}

        for row in MPV:
            if sanitize(row[1].lower()).startswith("e-folio a", 0, 9):
                efolio_A_cfg = fill_folio_cfg(row)

            if sanitize(row[1].lower()).startswith("e-folio b", 0, 9):
                efolio_B_cfg = fill_folio_cfg(row)

            if sanitize(row[1].lower()).startswith("e-folio c", 0, 9):
                efolio_C_cfg = fill_folio_cfg(row)

            if sanitize(row[1].lower()).startswith("p-folio", 0, 7):
                pfolio_cfg = fill_test_cfg(row)

            if row[1].lower().startswith("exame", 0, 5) and (row[2] is not None and "_global_" not in row[2].lower()):
                exame_cfg = fill_test_cfg(row)

        # pt: construir fórmula padrão da nota final
        # en: build final grade base formula
        if (len(efolio_A_cfg)) > 0 \
            and (len(efolio_B_cfg)) > 0 \
            and (len(efolio_C_cfg)) > 0 \
            and (len(pfolio_cfg)) > 0 \
            and (len(exame_cfg)) > 0:    
            correct_formula = "=max(sum(1-min(max(10*(sum("+\
                               "##gi" + str(efolio_A_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_B_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_C_cfg['id']) + "##"+\
                               ")-3.4),0),1),min(max(10*(sum("+\
                               "##gi" + str(efolio_A_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_B_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_C_cfg['id']) + "##"+\
                               ")-3.4),0),1)*min(max(10*("+\
                               "##gi" + str(pfolio_cfg['id']) + "##"+\
                               "-5.4),0),1)*min(max(10*(sum("+\
                               "##gi" + str(efolio_A_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_B_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_C_cfg['id']) + "##,"+\
                               "##gi" + str(pfolio_cfg['id']) + "##"+\
                               ")-9.4),0),1)*sum("+\
                               "##gi" + str(efolio_A_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_B_cfg['id']) + "##,"+\
                               "##gi" + str(efolio_C_cfg['id']) + "##,"+\
                               "##gi" + str(pfolio_cfg['id']) + "##"+\
                               ")),"+\
                               "##gi" + str(exame_cfg['id']) + "##"+\
                               ")"
        
        else:
            correct_formula = formula

        title = "\ndispositivos de avaliacao | MPV:"

        MPV = [row[1:] for row in MPV]
        table = tabulate(MPV, headers, tablefmt="grid", stralign="center") + "\n"

        print(sanitize(title + "\n" + table))

        time.sleep(1)

        # pt: isolar e validar fórmula da nota final
        # en: isolate and validate final grade formula
        T_items += 1

        query = "SELECT calculation \
                 FROM moodle.mdl_grade_items grd_it \
                 WHERE itemname = 'Nota final' \
                     AND grd_it.courseid = '" + course_ID + "';"
        mdl_db_cursor.execute(query)
        calculation = mdl_db_cursor.fetchall()

        if (len(calculation)) > 0:
            saved_formula = calculation[0][0]

            if saved_formula == correct_formula:
                formula = colored("OK", 'green')
                valPy_score += 1

        formula = "formula: " + formula

        print(sanitize(formula))

        time.sleep(1)

        # pt: validar somatório dos fólios
        # en: validate sum of folios
        T_items += 1

        if (len(efolio_A_cfg)) > 0 \
            and (len(efolio_B_cfg)) > 0 \
            and (len(efolio_C_cfg)) > 0 \
            and (len(pfolio_cfg)) > 0 \
            and (len(exame_cfg)) > 0:    

            if efolio_C_cfg["notatype"] == "Nota" \
                and (((efolio_A_cfg["grademax"] + efolio_B_cfg["grademax"] + efolio_C_cfg["grademax"]) == 8) \
                and ((efolio_A_cfg["grademax"] + efolio_B_cfg["grademax"] + efolio_C_cfg["grademax"] + pfolio_cfg['grademax']) == 20)) \
                or efolio_C_cfg["notatype"] != "Nota" \
                and (((efolio_A_cfg["grademax"] + efolio_B_cfg["grademax"]) == 8) \
                and ((efolio_A_cfg["grademax"] + efolio_B_cfg["grademax"] + pfolio_cfg['grademax']) == 20)):
                somatorio = colored("OK", 'green')
                valPy_score += 1

        somatorio = "somatorio: " + somatorio

        print(sanitize(somatorio))

        time.sleep(1)

        # pt: validar e-fólio A
        # en: validate e-folio A
        T_items += 1

        for item in items:
            if "e-folio a" in sanitize(item.text.lower()) and \
              ("trabalho" in item.text.lower() or \
               "assignment" in item.text.lower()):
                efolio_A = val_folio("efolioA", efolio_A_cfg)

                if (str(efolio_A_cfg['start']) != EMPTY_DATE and \
                    (str(decisao_end) != EMPTY_DATE and efolio_A_cfg['start'] <= decisao_end)):
                    efolio_A += colored(ERR_MSG_DTEARLY, 'yellow')

                break

        if efolio_A == "sim":
            efolio_A = colored("OK", 'green')
            valPy_score += 1

        efolio_A = "e-folio A: " + efolio_A

        print(sanitize(efolio_A))

        time.sleep(1)

        # pt: validar e-fólio B
        # en: validate e-folio B
        T_items += 1

        for item in items:
            if "e-folio b" in sanitize(item.text.lower()) and \
              ("trabalho" in item.text.lower() or \
               "assignment" in item.text.lower()):
                efolio_B = val_folio("efolioB", efolio_B_cfg)

                if (str(efolio_B_cfg['start']) != EMPTY_DATE and \
                    ((str(efolio_A_cfg['end']) != EMPTY_DATE and efolio_B_cfg['start'] <= efolio_A_cfg['end']) \
                    or (str(decisao_end) != EMPTY_DATE and efolio_B_cfg['start'] <= decisao_end))):
                    efolio_B += colored(ERR_MSG_DTEARLY, 'yellow')

                break

        if efolio_B == "sim":
            efolio_B = colored("OK", 'green')
            valPy_score += 1

        efolio_B = "e-folio B: " + efolio_B

        print(sanitize(efolio_B))

        time.sleep(1)

        # pt: validar e-fólio C
        # en: validate e-folio C
        for item in items:
            if "e-folio c" in sanitize(item.text.lower()) and \
              ("trabalho" in item.text.lower() or \
               "assignment" in item.text.lower()):
                if efolio_C_cfg["notatype"].lower() == "nota":
                    T_items += 1

                    efolio_C = val_folio("efolioC", efolio_C_cfg)

                    if (str(efolio_C_cfg['start']) != EMPTY_DATE and \
                        ((str(efolio_B_cfg['end']) != EMPTY_DATE and efolio_C_cfg['start'] <= efolio_B_cfg['end']) \
                        or (str(efolio_A_cfg['end']) != EMPTY_DATE and efolio_C_cfg['start'] <= efolio_A_cfg['end']) \
                        or (str(decisao_end) != EMPTY_DATE and efolio_C_cfg['start'] <= decisao_end))):
                        efolio_C += colored(ERR_MSG_DTEARLY, 'yellow')

                else:
                    efolio_C = colored("naoUtilizado", 'dark_grey')

                break

        if efolio_C == "sim":
            efolio_C = colored("OK", 'green')
            valPy_score += 1

        efolio_C = "e-folio C: " + efolio_C

        print(sanitize(efolio_C))

        time.sleep(1)

        # pt: validar p-fólio
        # en: validate p-folio
        T_items += 1

        for item in items:
            if "p-folio" in sanitize(item.text.lower()) and \
              ("trabalho" in item.text.lower() or \
               "assignment" in item.text.lower()):
                pfolio = val_test("pfolio", pfolio_cfg, 12, "contínua")

                break

        if pfolio == "sim":
            pfolio = colored("OK", 'green')
            valPy_score += 1

        pfolio = "p-folio: " + pfolio

        print(sanitize(pfolio))

        time.sleep(1)

        # pt: validar exame
        # en: validate exam
        T_items += 1

        for item in items:
            if "exame" in item.text.lower() and \
              ("trabalho" in item.text.lower() or \
               "assignment" in item.text.lower()):
                exame = val_test("exame", exame_cfg, 20, "exame")

                break

        if exame == "sim":
            exame = colored("OK", 'green')
            valPy_score += 1

        exame = "exame: " + exame

        print(sanitize(exame))

        time.sleep(1)
    
    if UC_type == 1:
        # identificar tópico WISEflow
        # T_items += 1

        # query = "SELECT * \
        #          FROM moodle.mdl_course_sections \
        #          WHERE name LIKE '%AVALIAÇÃO%|%WISEflow%' \
        #              AND course = '" + course_ID + "';"
        # mdl_db_cursor.execute(query)
        # myresult = mdl_db_cursor.fetchall()

        # if len(myresult) != 0:
        #     topico_WISEflow = "sim"

        #     if len(myresult) > 1:
        #         topico_WISEflow += colored(ERR_MSG_MULTI, 'yellow')

        #     if myresult[0][7] != 1:
        #         topico_WISEflow += colored(ERR_MSG_HIDDEN, 'yellow')

        # if topico_WISEflow == "sim":
        #     topico_WISEflow = colored("OK", 'green')
        #     valPy_score += 1

        # topico_WISEflow = "topico WISEflow: " + topico_WISEflow

        # print(sanitize(topico_WISEflow))

        # time.sleep(1)

        # pt: identificar dispositivos das PEEs
        # en: identify electronic written exams devices
        # title = "\ndispositivos de avaliacao | PEEs:"

        # PEEs = [row[1:] for row in PEEs]
        # table = tabulate(PEEs, headers, tablefmt="grid", stralign="center") + "\n"

        # print(sanitize(title + "\n" + table))

        # time.sleep(1)

        # identificar dispositivo flow_type
        T_items += 1

        query = "SELECT * \
                 FROM moodle.mdl_course_modules \
                 WHERE idnumber LIKE 'flow_type' \
                     AND course = '" + course_ID + "';"
        mdl_db_cursor.execute(query)
        myresult = mdl_db_cursor.fetchall()

        if len(myresult) != 0:
            flow_type = "sim"

            if len(myresult) > 1:
                flow_type += colored(ERR_MSG_MULTI, 'yellow')

        if flow_type == "sim":
            flow_type = colored("OK", 'green')
            valPy_score += 1

        flow_type = "dispositivo Flow_Type: " + flow_type

        print(sanitize(flow_type))

        time.sleep(1)

    # pt: identificar e verificar imagens
    # en: identify and validate images
    pic_tags = []

    pics = page.find_all('img')

    headers = ["fonte",
               "resultado",
               "dimensoes",
               "watermark"]
    
    if len(pics) > 0:
        T_items += 1

        title = "\nimagens:"
        print(sanitize(title))

        for pic in tqdm(pics):
            if len(pic.get('src')) < 150:
                try:
                    try_link = requests.get(pic.get('src'), timeout=5)

                except SSLError:
                    result = ERR_SSL

                except Exception:
                    result = ERR_NOREPLY

                if try_link.status_code == 200:
                    if pic.get('title') is not None:
                        result = "OK: " + pic.get('title')
                        
                    else:
                        result = OK_NOTITLE

                    try:
                        with Image.open(BytesIO(try_link.content)) as img:
                            size = img.size

                            if detect_watermark(img):
                                watermark = "sim/talvez"

                            else:
                                watermark = "nao"

                    except Exception:
                        size = "ND"
                        watermark = "ND"

                else:
                    result = "erro: imagem invalida"

            else:
                result = "erro: fonte suspeita (URL com " + str(len(pic.get('src'))) + " caracteres)"

            if 'erro' in result:
                T_pnlt = 1

            pic_tags.append([pic.get('src')[:100], result, size, watermark])

        table = tabulate(pic_tags, headers, tablefmt="pretty", stralign="left") + "\n"

        if T_pnlt == 0:
            valPy_score += 1

        else:
            T_pnlt = 0

        print(sanitize(table))

    else:
        none = "imagens: " + colored("nenhuma imagem adicionada", "dark_grey") + "\n"
        print(none)

    # pt: validar URLs adicionados na UC
    # en: validate URLs added to the course
    links = []

    query = "SELECT DISTINCT externalurl \
             FROM moodle.mdl_url \
             WHERE course = '" + course_ID + "';"
    mdl_db_cursor.execute(query)
    DB_links = mdl_db_cursor.fetchall()

    page = BeautifulSoup(page2validate.content, "html.parser")
    page_links = []
    for a_tag in page.find_all("a", href=True):
        page_links.append(a_tag["href"])

    headers = ["URL",
               "resultado"]
    
    # TODO: passar links a excluir para o bloco Moodle
    links2check = DB_links + [(link,) for link in page_links if "elearning.uab.pt" not in link
                                                             and "#" not in link
                                                             and "moodle" not in link
                                                             and "wiseflow" not in link
                                                             and "portal.uab.pt" not in link
                                                             and "netpa.uab.pt" not in link
                                                             and "arquivo.uab.pt" not in link
                                                             and "sitcon.uab.pt" not in link
                                                             and "AvalDocentes" not in link
                                                             and "prezi.com/p/p16bbu2vvx8e" not in link
                                                             and "prezi.com/embed/nbcuhusgrwx3" not in link
                                                             and "facebook.com/universidadeaberta.portugal" not in link
                                                             and "twitter.com/uaberta" not in link
                                                             and "instagram.com/universidadeabertaportugal" not in link
                                                             and "linkedin.com/school/universidade-aberta" not in link
                                                             and "youtube.com/user/UAbPT" not in link
                                                             and "brunomastavares"not in link]

    if len(links2check) > 0:
        T_items += 1

        title = "URLs:"
        print(sanitize(title))

        for link in tqdm(links2check):
            if link[0].find(str(urlparse(wwwroot).netloc)) == -1:
                try:
                    try_link = requests.get(link[0], timeout=5)

                except SSLError:
                    result  = ERR_SSL

                except Exception:
                    result = ERR_NOREPLY

                if try_link.status_code == 200:
                    page = BeautifulSoup(try_link.content, HTML_PARSER)

                    if page.title is not None:
                        result = "OK: " + page.title.text
                        
                    else:
                        result = OK_NOTITLE

                else:
                    result = ERR_URL

                if 'erro' in result:
                    T_pnlt = 1

                links.append([link[0], result])

        table = tabulate(links, headers, tablefmt="pretty", stralign="left") + "\n"

        if T_pnlt == 0:
            valPy_score += 1

        else:
            T_pnlt = 0

        print(sanitize(table))

    else:
        none = "URLs: " + colored("nenhum URL adicionado", "dark_grey") + "\n"
        print(none)

    # pt: identificar iframes
    # en: identify iframes
    ifrm_tags = []

    iframes = page.find_all('iframe')

    headers = ["fonte",
               "resultado",
               "dimensoes",
               "parametros"]
    
    if len(iframes) > 0:
        T_items += 1

        title = "conteudos embebidos (iframes):"
        print(sanitize(title))

        for iframe in tqdm(iframes):
            try:
                src = iframe['src']

            except Exception:
                try:
                    src = iframe['data-src']

                except Exception:
                    src = None

            try:
                width = iframe['width']

            except Exception:
                width = None

            try:
                height = iframe['height']

            except Exception:
                height = None

            try:
                params = iframe['style']

            except Exception:
                params = "ND"            

            if width is not None and height is not None:
                size = "(" + str(width) + ", " + str(height) + ")"
            
            else:
                size = "ND"

            try:
                try_link = requests.get(src, timeout=5)

            except SSLError:
                result  = ERR_SSL

            except Exception:
                result = ERR_NOREPLY

            if try_link.status_code == 200:
                page = BeautifulSoup(try_link.content, HTML_PARSER)

                if page.title is not None:
                    result = "OK: " + page.title.text
                    
                else:
                    result = OK_NOTITLE

            else:
                result = ERR_URL

            if 'erro' in result:
                T_pnlt = 1

            ifrm_tags.append([src, result, size, params])

        table = tabulate(ifrm_tags, headers, tablefmt="pretty", stralign="left") + "\n"

        if T_pnlt == 0:
            valPy_score += 1

        else:
            T_pnlt = 0

        print(sanitize(table))

    else:
        none = "conteudos embebidos (iframes): " + colored("nenhuma iframe adicionada", "dark_grey") + "\n"
        print(none)

    # pt: fechar ligação à BD
    # en: close DB connection
    mdl_db_cursor.close()
    mdl_db.close()

    valPy_score = round((valPy_score/T_items)*100, 2)

    if valPy_score < 70:
        color = "red"

    elif valPy_score < 100:
        color = "yellow"

    else:
        color = "green"

    print("\nval.Py score: " + colored(str(valPy_score) + "%\n", color))

    return valPy_score

if __name__ == "__main__":
    main()
