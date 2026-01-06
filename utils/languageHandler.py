from __future__ import unicode_literals
from builtins import zip
from builtins import str
import builtins
import os
import sys
import ctypes
import locale
import gettext
import platform
#a few Windows locale constants
LOCALE_SLANGUAGE=0x2
LOCALE_SLANGDISPLAYNAME=0x6f
curLang="es"
def localeNameToWindowsLCID(localeName):
    """Retreave the Windows locale identifier (LCID) for the given locale name
    @param localeName: a string of 2letterLanguage_2letterCountry or or just 2letterLanguage
    @type localeName: string
    @returns: a Windows LCID
    @rtype: integer
    """ 
    #Windows Vista is able to convert locale names to LCIDs
    func_LocaleNameToLCID=getattr(ctypes.windll.kernel32,'LocaleNameToLCID',None)
    if func_LocaleNameToLCID is not None:
        localeName=localeName.replace('_','-')
        LCID=func_LocaleNameToLCID(str(localeName),0)
    else: #Windows doesn't have this functionality, manually search Python's windows_locale dictionary for the LCID
        localeName=locale.normalize(localeName)
        if '.' in localeName:
            localeName=localeName.split('.')[0]
        LCList=[x[0] for x in locale.windows_locale.items() if x[1]==localeName]
        if len(LCList)>0:
            LCID=LCList[0]
        else:
            LCID=0
    return LCID

def getLanguageDescription(language):
    """Finds out the description (localized full name) of a given local name"""
    desc=None
    if platform.system() == "Windows":
        LCID=localeNameToWindowsLCID(language)
        if LCID!=0:
            buf=ctypes.create_unicode_buffer(1024)
            if '_' not in language:
                res=ctypes.windll.kernel32.GetLocaleInfoW(LCID,LOCALE_SLANGDISPLAYNAME,buf,1024)
            else:
                res=0
            if res==0:
                res=ctypes.windll.kernel32.GetLocaleInfoW(LCID,LOCALE_SLANGUAGE,buf,1024)
            desc=buf.value
    return desc
def getAvailableLanguages():
    """generates a list of locale names, plus their full localized language and country names.
    @rtype: list of tuples
    """
    #Make a list of all the locales found in NVDA's locale dir
    l=[x for x in os.listdir('locales') if os.path.isfile(os.path.join('locales', x, 'LC_MESSAGES', 'VeTube.mo'))]
    #Make sure that es (spanish) is in the list as it may not have any locale files, but is default
    if 'es' not in l:
        l.append('es')
        l.sort()
    #For each locale, ask Windows for its human readable display name
    d=[]
    for i in l:
        desc=getLanguageDescription(i)
        label="%s, %s"%(desc,i) if desc else i
        d.append(label)
    #include a 'user default, windows' language, which just represents the default language for this user account
    l.append("system")
    # Translators: the label for the Windows default NVDA interface language.
    d.append(_("Idioma del sistema"))
    #return a zipped up version of both the lists (a list with tuples of locale,label)
    return list(zip(l,d))

def makePgettext(translations):
    """Obtaina  pgettext function for use with a gettext translations instance.
    pgettext is used to support message contexts,
    but Python 2.7's gettext module doesn't support this,
    so NVDA must provide its own implementation.
    """
    if isinstance(translations, gettext.GNUTranslations):
        def pgettext(context, message):
            message = str(message)
            try:
                # Look up the message with its context.
                return translations._catalog["%s\x04%s" % (context, message)]
            except KeyError:
                return message
    else:
        def pgettext(context, message):
            return str(message)
    return pgettext

def setLanguage(lang):
    system = platform.system()
    global curLang
    try:
        if lang=="system":
            if system == "Windows":
                windowsLCID=ctypes.windll.kernel32.GetUserDefaultUILanguage()
                localeName=locale.windows_locale[windowsLCID]
            trans=gettext.translation('VeTube', localedir='locales', languages=[localeName])
            curLang=localeName
        else:
            trans=gettext.translation('VeTube', localedir='locales', languages=[lang])
            curLang=lang
            localeChanged=False
            if system == "Windows":
                locale.setlocale(locale.LC_ALL, langToWindowsLocale(lang))
                localeChanged=True
            else:
                locale.setlocale(locale.LC_ALL, lang)
                localeChanged=True
            if not localeChanged and '_' in lang:
                try:
                    locale.setlocale(locale.LC_ALL, lang.split('_')[0])
                except:
                    pass
            if system == "Windows":
                LCID=localeNameToWindowsLCID(lang)
                ctypes.windll.kernel32.SetThreadLocale(LCID)
    except IOError:
        trans=gettext.translation('VeTube', fallback=True)
        curLang="es"
    if sys.version[0] == "3":
        trans.install()
    else:
        trans.install(unicode=True)

def getLanguage():
    return curLang

def normalizeLanguage(lang):
    """
    Normalizes a  language-dialect string  in to a standard form we can deal with.
    Converts  any dash to underline, and makes sure that language is lowercase and dialect is upercase.
    """
    lang=lang.replace('-','_')
    ld=lang.split('_')
    ld[0]=ld[0].lower()
    #Filter out meta languages such as x-western
    if ld[0]=='x':
        return None
    if len(ld)>=2:
        ld[1]=ld[1].upper()
    return "_".join(ld)
def langToWindowsLocale(lang):
    languages = {"en": "eng",
                 "ar": "ara",
                 "ca": "cat",
                 "de": "deu",
                 "es": "esp",
                 "fi": "fin",
                 "fr": "fre_FRA",
                 "gl": "glc",
                 "eu": "euq",
                 "hu": "hun",
                 "hr": "hrv",
                 "it": "ita",
                 "ja": "jpn",
                 "pl": "plk",
                 "pt": "ptb",
                 "ru": "rus",
                 "tr": "trk",
                 "sr": "eng",
                 "id": "ind",
                 "cs": "csy"
                 }
    return languages[lang]