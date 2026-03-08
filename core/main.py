#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SpeedScan - VersÃ£o 1.0.0
# Desenvolvedor: Ewerton Vasconcelos

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging
import os
import platform
import threading
import json
import sys
import re
import time
import subprocess
from PIL import Image, ImageDraw
import psutil
import customtkinter as ctk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ImportaÃ§Ãµes dos mÃ³dulos internos
from core import config
from core.hardware import HardwareInfo
from core.actions import CommandRunner, ActionMapper, ActionHandler  # Agora importamos o ActionHandler completo de core.actions
from core.scheduler import Scheduler
from core import ui
from core.health_score import HealthScore
from core.temperature_monitor import TemperatureMonitor
from core.smart_monitor import SmartMonitor
from core.browser_cleaner import BrowserCleaner
from core.speed_test import SpeedTester
from core.process_manager import ProcessManager
from core.historical_metrics import MetricsCollector, MetricsDB
from core.lan_scanner import LANScanner
from core.ai_proactive import AIProactive
from core.security_scanner import SecurityScanner
from core.dashboard import Dashboard
from core.lan_cache import LANCacheManager
from core.chat import ChatFrame
from core.first_run import FirstRunWizard
from core.cookie_manager import CookieManager
from core.trash_manager import TrashManager

# ConfiguraÃ§Ã£o de logging
config.LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = config.LOG_DIR / "speedscan.log"
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(\Øİ[YJ\ÈH	J˜[YJ\ÈH	J]™[˜[YJ\ÈH	JY\ÜØYÙJ\ÉÊBš[™\‹œÙ]›Ü›X]\Š›Ü›X]\ŠB›ÙÙÚ[™Ë˜˜\ÚXĞÛÛ™šYÊ]™[[ÙÙÚ[™Ë‘T”“Ô‹[™\œÏVÚ[™\—JB‚ˆÈOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOBˆÈÛÛ™šYİ\˜péğèÛÈY°èÛÈ[šYšXØYBˆÈOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOB‘QUSĞÓÓ‘’QÈHÂˆ[YHˆ™Y˜][‹ˆ\Ù\›˜[YHˆ™]Ù\Ûˆ‹ˆ›[™İXYÙHˆœĞ”ˆ‹ˆZWÜØØ[Hˆ˜]]È‹ˆ›Ü[—Ùš[WÚ[—İXˆˆ˜[ÙKˆœÚ[\WÛ[ÙHˆYKˆ™^\Û]™[ˆKˆÚ[™İ×Üİ]HˆÂˆ›X^[Z^™Yˆ˜[ÙKˆÚYˆLˆšZYÚˆÌˆˆ›Û™KˆHˆ›Û™BˆKˆœØÚY[HˆÂˆ™[˜X›Yˆ˜[ÙKˆ™œ™\]Y[˜ŞHˆÙYZÛH‹ˆšİ\ˆˆŒÎŒ‹ˆ™^WÛÙ—İÙYZÈˆ›[Û™^H‹ˆ™^WÛÙ—Û[ÛˆKˆš[\˜[Ù^\ÈˆËˆ\ÚÜÈˆÈ˜ØXÚH‹œİØ\‹˜ÚXÚÈ—Kˆ™[]˜]Yˆ˜[ÙBˆKˆ˜ZHˆÂˆœ›İšY\ˆˆ›Û[XH‹ˆ›[Ù[ˆ›[XLËŒˆ‹ˆ˜\WÚÙ^Hˆˆ‹ˆ™[™Ú[ˆš‹ËÛØØ[ÜİŒLMÍ‚ˆBŸB‚ˆÈOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOBˆÈYš[špéğèÛÈH[X\ËY[ÛX\Ë\ØØ[\ÈHİYÙ\İ0íY\ÈHPBˆÈOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOB•SQTÈHÂˆ™Y˜][ˆÈ›[ÙHˆ™\šÈ‹˜™ÈˆˆÌYLLØˆ‹œÚYHˆˆÌŒMÌ˜H‹˜XØÈˆˆØNMYÈ‹^ˆˆÙ™™™™™ˆŸKˆ™Ü™^HˆÈ›[ÙHˆ›YÚ‹˜™ÈˆˆÙYYˆ‹œÚYHˆˆÌÍÍMLH‹˜XØÈˆˆÍMMŒÈ‹^ˆˆÌLLNÈŸKˆ™\šÈˆÈ›[ÙHˆ™\šÈ‹˜™ÈˆˆÌ‹œÚYHˆˆÌ‹˜XØÈˆˆÌLNH‹^ˆˆÙ™™™™™ˆŸKˆ›YÚˆÈ›[ÙHˆ›YÚ‹˜™ÈˆˆÙ™™™™™ˆ‹œÚYHˆˆÙ˜Y˜È‹˜XØÈˆˆÌMŒÙXˆ‹^ˆˆÌŒMÌ˜HŸBŸB‚“S‘ÕPQÑTÈHÂˆœĞ”ˆˆ”ÜYİpê\Èœ˜\Ú[Z\›È‹ˆ™[—ÕTÈˆ‘[™Û\Ú
TÊH‹ˆ™\×ÑTÈˆ‘\Üpì[Û‚ŸB‚”ĞĞSTÈHÂˆ˜]]Èˆ]]Ûpè]XÛÈ‹ˆŒLˆŒL	H‹ˆŒLHˆŒLIH‹ˆŒMLˆŒML	H‚ŸB‚RWÔÕQÑÑTÕSÓ”ÈHÂˆ“Û[XH
ØØ[
H‹“Ü[RHÔ‹‘ÛÛÙÛHÙ[Z[šH‹Û]YH
[›ÜXÊH‹ˆ“[XHÈ
Y]JH‹“Z\İ˜[RH‹ÛÚ\™H‹‘Y\ÙYZÈ‹ÛÛ™šYİ\™HØØ[RH‚—B‚ˆÈOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOBˆÈÛ\ÜÙHš[˜Ú\[ÜYYØØ[‚ˆÈOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOB˜Û\ÜÈÜYYØØ[ŠİËÕÊN‚ˆˆˆ’˜[™[Hš[˜Ú\[È\XØ]]›Ëˆˆˆ‚‚ˆYˆ×Ú[š]×ÊÙ[ŠN‚ˆİ\\Š
K—×Ú[š]×Ê
BˆÙ[‹”ÓÈH]›Ü›KœŞ\İ[J
BˆÙ[‹œ[›™\ˆHÛÛ[X[™[›™\ŠÙ[‹”ÓÊBˆÙ[‹šÈH\™Ø\™R[™›ÊÙ[‹”ÓËÙ[‹œ[›™\ŠBˆÙ[‹˜ÛÛ™šYÈHÙ[‹—ÛØYØÛÛ™šYÊ
BˆÙ[‹\]Wİ[YWİ˜\œÊ
BˆÙ[‹]Jˆ”ÜYYØØ[ˆØÛÛ™šYË•‘T”ÒSÓŸHŠBˆÙ[‹˜ÛÛ™šYİ\™J™×ØÛÛÜ\Ù[‹˜™×ØÛÛÜŠBˆÙ[‹›Z[œÚ^™JLŒ
BˆÙ[‹˜\WİZWÜØØ[J
BˆÙ[‹\˜›×ØXİ]™HH˜[ÙBˆÙ[‹˜ÛÛœÛÛ\×İš\ÚX›HHßBˆÙ[‹œ[™×ØXİ]™HH˜[ÙBˆÙ[‹˜İ\œ™[Û[Ù[HH™\Ú›Ø\™‚ˆÙ[‹œÚYX˜\—Ø]ÛœÈHßBˆÙ[‹™]Z[Ø]ÛœÈHßBˆÙ[‹›ÙÜÈHßB‚ˆÙ[‹šX[Û[Ûš]ÜˆHX[ØÛÜ™J
BˆÙ[‹šX[ÜØÛÜ™Wİ˜\ˆHİË”İš[™Õ˜\Š˜[YOHØ[İ[[™Ë‹‹ˆŠBˆÙ[‹[\Û[Ûš]ÜˆH[\\˜]\™S[Ûš]ÜŠ
BˆÙ[‹œÛX\Û[Ûš]ÜˆHÛX\[Ûš]ÜŠ
BˆÙ[‹˜œ›İÜÙ\—ØÛX[™\ˆHœ›İÜÙ\ÛX[™\Š
BˆÙ[‹œÜYYİ\İ\ˆHÜYY\İ\Š
BˆÙ[‹œ›Ø×ÛX[˜YÙ\ˆH›ØÙ\ÜÓX[˜YÙ\Š
BˆÙ[‹›Y]šXÜ×ØÛÛXİÜˆHY]šXÜĞÛÛXİÜŠ[\˜[MJBˆÙ[‹›Y]šXÜ×ÙˆHY]šXÜÑŠ
BˆÙ[‹›[—ÜØØ[›™\ˆHS”ØØ[›™\Š
BˆÙ[‹˜ZWÜ›ØXİ]™HHRT›ØXİ]™JÙ[‹›Y]šXÜ×Ù‹Ù[‹šX[Û[Ûš]ÜŠBˆÙ[‹œÙXİ\š]WÜØØ[›™\ˆHÙXİ\š]TØØ[›™\ŠÙ[‹”ÓÊBˆÙ[‹›[—ØØXÚHHSØXÚSX[˜YÙ\ŠÙ[‹”ÓÊBˆÙ[‹˜ÛÛÚÚYWÛX[˜YÙ\ˆHÛÛÚÚYSX[˜YÙ\Š
BˆÙ[‹˜\ÚÛX[˜YÙ\ˆH˜\ÚX[˜YÙ\Š
BˆÙ[‹›Y]šXÜ×ØÛÛXİÜ‹œİ\

BˆÙ[‹œ›Ø×ÛX[˜YÙ\‹œİ\Û[Ûš]Üš[™Ê
B‚ˆÈYÛÜ˜H\Ø[[ÜÈÈXİ[Û’[™\ˆ[\ÜYÈHÛÜ™K˜Xİ[ÛœÂˆÙ[‹˜Xİ[Û—Ú[™\ˆHXİ[Û’[™\ŠÙ[ŠB‚ˆÙ[‹™ÜšYØÛÛ[[˜ÛÛ™šYİ\™JKÙZYÚLJBˆÙ[‹™ÜšYÜ›İØÛÛ™šYİ\™JÙZYÚLJB‚ˆÙ[‹—ØZ[ÜÚYX˜\Š
B‚ˆÙ[‹˜ÛÛZ[™\ˆHİËÕÑœ˜[YJÙ[‹™×ØÛÛÜH˜[œÜ\™[ŠBˆÙ[‹˜ÛÛZ[™\‹™ÜšY
›İÏLÛÛ[[LKİXÚŞOH›œÙ]È‹YLŒYOLŒ
BˆÙ[‹˜ÛÛZ[™\‹™ÜšYØÛÛ[[˜ÛÛ™šYİ\™JÙZYÚLJBˆÙ[‹˜ÛÛZ[™\‹™ÜšYÜ›İØÛÛ™šYİ\™JÙZYÚLJB‚ˆÙ[‹™œ˜[Y\ÈHßBˆ›Üˆˆ[ˆÙ[‹™]Z[Ø]ÛœË˜[Y\Ê
N‚ˆ‹œXÚ×Ù›Ü™Ù]

BˆÙ[‹˜ÛÛœÛÛ\×İš\ÚX›HHİYÎˆ˜[ÙH›ÜˆYÈ[ˆÙ[‹™]Z[Ø]ÛœËšÙ^\Ê
_B‚ˆÙ[‹œÚİ×Ùœ˜[YJ™\Ú›Ø\™ŠBˆÙ[‹—ÜÙ]\Øš[™[™ÜÊ
Bˆ™XY[™Ë•™XY
\™Ù]\Ù[‹—Û[Ûš]Ü—ÛÛÜY[[ÛUYJKœİ\

BˆÙ[‹—ØÚXÚ×Ü›ØÙ\Ü×Ü]Y]YJ
BˆÙ[‹˜Y\ŠŒÙ[‹—Ü™\İÜ™WİÚ[™İ×Üİ]JBˆÙ[‹œ›İØÛÛ
•ÓWÑSUWÕÒS‘ÕÈ‹Ù[‹—ÛÛ—ØÛÜÚ[™ÊBˆÙ[‹˜Y\ŠLÙ[‹—ØÚXÚ×Ùš\œİÜ[ŠB