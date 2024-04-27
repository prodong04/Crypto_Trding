# ./scripts/cluster_retrieval.sh 파일 실행해서 분류
import os
import pandas as pd
import numpy as np
import random
import json
import argparse
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, pipeline


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--set_dir',type=str,help='set woking directory')
    parser.add_argument('--model',type=str,default='Ehsanl/Roberta-DNLI')
    parser.add_argument('--key_data',type=str)
    parser.add_argument('--song_data',type=str)
    parser.add_argument('--n_cluster',type=int, help='number of clusters')
    parser.add_argument('--n_sample',type=int, help='number of samples used from each cluster for cluster selection')
    parser.add_argument('--n_songs',type=int,help='number of songs in final playlist')
    args = parser.parse_args()

    return args


def read_json(path):
    json_objects = pd.read_json(path,encoding='utf-8')
    return json_objects.to_dict('records')


def load_songs(args):
    print('**** Loading song data ... ****')
    songs = read_json(args.song_data)
    return songs


def group_by_cluster(songs, n_cluster):
    '''
    songs 데이터를 cluster별로 분류
    return format: [[cluster_1],[cluster_2],...,[cluster_n]]
    '''
    print('**** Sorting Songs by Clusters ... ****')

    cluster = []
    for n in range(n_cluster):
        cluster.append([])
  
    for idx in tqdm(range(len(songs))):
        song = songs[idx]
        cluster[song['cluster']].append(song)
    
    print('**** Sorting completed !!! ****')
    return cluster 


def load_keyword(args):
    '''
    keyword file format이 리스트 한줄짜리 json이라고 가정
    input format : {"keywords":["줄거리키워드1","줄거리키워드2"]}
    output format : "줄거리키워드1 줄거리키워드2"
    
    ### book crawler 완성 이후 input() 함수로 사용자에게 input 받게끔 수정 ###
    '''
    print('**** Loading keyword input ****')
    with open(args.key_data,'r',encoding='utf-8') as f:
        keywords = [json.loads(line) for line in f]
        keywords = ' '.join(keywords[0]['keywords'])

    return keywords # dtype: str


def pick_random_sample(cluster,n_sample):
    '''
    각 cluster에서 랜덤으로 n개의 샘플 추출하여 리턴
    return format : { 1:[cluster_1_samples], ..., n:[cluster_n_samples] }
    '''
    print('**** Random Sampling from each cluster ... ****')

    random_samples = {}
    for i in range(len(cluster)):
        random_sample = random.choices(cluster[i], k=n_sample)
        random_samples[i] = random_sample
    print('**** random sampling done ****')
    
    return random_samples
        

def load_model(args):
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = pipeline("text-classification", model=args.model,device="cpu")
    return model, tokenizer


def model_scoring(keywords, song_list, model, tokenizer):
    '''
    keyword와 각각의 song의 가사를 짝지어 데이터셋 구축
        - cluster selection 단계: song_list = random_samples[n]
        - cluster scoring 단계: song_list = selected_cluster 
            selected_cluster format : [{song},{song},{song},{song}]
    ############# song['lyrics']로 가정 ################
    '''
    # formatting inputs
    inputs = []
    keyword_lst = []
    track_name = []
    artist_name = []
    lyrics = []

    for song in tqdm(song_list):
        track_name.append(song['track_name'])
        artist_name.append(song['artist_name'])
        lyrics.append(song['lyrics'])
        keyword_lst.append(keywords)
        input = keywords + ' ' + tokenizer.sep_token + ' ' + song['lyrics']
        inputs.append(input)


    # model infernece
    outputs = model(inputs)
    output_dic = []
    for keyword, track_name, artist_name, output in zip(keyword_lst, track_name, artist_name, outputs):
        dic = {'track_name': track_name,
               'artist_name': artist_name,
               'keyword': keyword,
               'lyrics': lyrics,
               'predicted_label': output['label'],
               'predicted_score': output['score']}
    output_dic.append(dic)

    return output_dic


def select_cluster(random_samples,keywords,model,tokenizer):
    mean_score = {}

    # 각 cluster별로 다음을 시행
    for n in range(len(random_samples)):
        output_dic = model_scoring(keywords=keywords,
                                   song_list=random_samples[n],
                                   model=model,
                                   tokenizer=tokenizer)
        
        score = []
        for output in output_dic:
            if output['predicted_label']=='ENTAILMENT': #레이블이 entailment인 것만 scoring
                score.append(output['predicted_score'])

        # 클러스터별로 평균 내기
        if len(score)==0:
            score = 0
        else: 
            score = np.mean(score)

        mean_score[n] = score
        
    return max(mean_score,key=mean_score.get) # mean score가 가장 높은 cluster number 리턴


def playlist_recommendation(output_dic, n_songs):

    df = pd.DataFrame(output_dic)
    df_ent = df[ df['predicted_label']=='ENTAILMENT' ]
    playlist_df = df_ent[['track_name','artist_name','predicted_score']].sort_values(by=['predicted_score'],ascending=False)
    
    if len(playlist_df)<=n_songs:
        result = playlist_df
    else:
        result = playlist_df.iloc[:n_songs,:]

    return result


#TODO??
'''def save_results:'''


def main(args):

    os.chdir(args.set_dir)

    model,tokenizer = load_model(args)

    # Load song & keyword data
    songs = load_songs(args)
    keywords = load_keyword(args)

    # cluster selection
    cluster = group_by_cluster(songs, args.n_cluster)
    random_samples = pick_random_sample(cluster,args.n_sample)
    selected_cluster = cluster[select_cluster(random_samples=random_samples,
                                              keywords=keywords,
                                              model=model,
                                              tokenizer=tokenizer)]

    # playlist composition
    output_dic = model_scoring(keywords=keywords, 
                  song_list=selected_cluster,
                  model=model,
                  tokenizer=tokenizer)
    playlist = playlist_recommendation(output_dic=output_dic, n_songs=args.n_songs)

    print('\n#############################################\n  RECOMMENDED PLAYLIST: \n')
    print(playlist)
    print('\n#############################################')


if __name__ == '__main__':
    args = parse_args()
    main(args)