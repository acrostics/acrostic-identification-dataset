#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path" || exit

curl -o ./enwikisource.xml.bz2 https://dumps.wikimedia.org/enwikisource/20240420/enwikisource-20240420-pages-meta-current.xml.bz2
bzip2 -d enwikisource.xml.bz2
curl -o ./frwikisource.xml.bz2 https://dumps.wikimedia.org/frwikisource/20240501/frwikisource-20240501-pages-meta-current.xml.bz2
bzip2 -d frwikisource.xml.bz2
curl -o ./ruwikisource.xml.bz2 https://dumps.wikimedia.org/ruwikisource/20240501/ruwikisource-20240501-pages-meta-current.xml.bz2
bzip2 -d ruwikisource.xml.bz2
cd wikiextractor && python3 -m wikiextractor.WikiExtractor ../enwikisource.xml -o ../en/ -ns Author,Index,Category,Template,Portal,Wikisource,Module,MediaWiki,Help && cd ../
cd wikiextractor && python3 -m wikiextractor.WikiExtractor ../ruwikisource.xml -o ../ru/ -ns Автор,Индекс,Участник,Обсуждение,Категория,Шаблон,Портал,Викитека,Модуль,Медивики,MediaWiki,Справка && cd ../
cd wikiextractor && python3 -m wikiextractor.WikiExtractor ../frwikisource.xml -o ../fr/ -ns Auteur,Modèle,Wikisource,MediaWiki,Portail,Module,Aide,Catégorie,Discussion && cd ../