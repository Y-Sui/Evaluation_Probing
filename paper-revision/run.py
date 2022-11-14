import os

os.environ["CUDA_VISIBLE_DEVICES"] = "3" # set the cuda card 2,3,4,5
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import logging
import wandb
import torch
from dataloader import DEFALT_DATASETS, DEFALT_LANGUAGES, EvaluationProbing, DEFALT_NUM_LABELS, TAG_DICT_WIKIANN
from model import DEFAULT_MODEL_NAMES, DEFAULT_EMBED_SIZE, MBertLayerWise, MBertHeadWise, XLMRHeadWise, XLMRLayerWise
from trainer import EvalTrainer

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

def get_arguments():
    # Required parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_config", default="M-BERT", choices=DEFAULT_MODEL_NAMES.keys(), type=str,
                        help="Name of the pretrained model")
    parser.add_argument("--tokenizer_config", default="bert-base-multilingual-cased", choices=DEFAULT_MODEL_NAMES.keys(), type=str,
                        help="Name of the pretrained tokenizer")
    parser.add_argument("--corpus", default="pawsx", choices=DEFALT_DATASETS.keys(), type=str)
    parser.add_argument("--lang", default="en", type=str)
    parser.add_argument("--tag_class", default="PER", type=str, choices=["PER", "LOC", "ORG"], help="only work when the corpus sets to wikiann")
    parser.add_argument("--embed_size", default="large", choices=DEFAULT_EMBED_SIZE.keys(), type=str)
    parser.add_argument("--classifier_num", default=2, choices=[1,2,3,4,5], type=int)
    parser.add_argument("--max_length", default=100, type=int, help="Max length of the tokenization")
    parser.add_argument("--fc", default="probing", type=str, choices=['probing', 'finetune'], help="choose which training strategies will be applied")

    # Options parameters
    parser.add_argument("--cache_dir", default=None, type=str,
                        help="Where do you want to store the pre-trained models downloaded from s3", )
    parser.add_argument("--batch_size", default=128, type=int, help="Batch size.")
    parser.add_argument("--no_shuffle", action="store_true", help="Whether not to shuffle the dataloader")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no_cuda", action="store_true", help="Whether not to use CUDA when available")
    parser.add_argument("--epochs", default=3, type=int)
    parser.add_argument("--num_workers", default=0, type=int)
    parser.add_argument("--lr", default=0.0001, type=float)
    parser.add_argument("--profile", action="store_true", help="whether to generate the heatmap")
    parser.add_argument("--mode", choices=["layer-wise", "head-wise"], type=str, help="choose training mode")
    parser.add_argument("--checkpoints", type=str, default="/home/weicheng/data_interns/yuansui/models/xnli/M-BERT_finetune/")
    args = parser.parse_args()

    # Setup devices (No distributed training here)
    args.device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    args.num_labels = DEFALT_NUM_LABELS[args.corpus]

    return args

def main(args):
    logger = logging.getLogger("Run()")
    evaluation_probing_loader = EvaluationProbing(args)
    dataloader = evaluation_probing_loader.get_dataloader()
    args.pad_token_id = evaluation_probing_loader.pad_token_id

    # if args.lang not in DEFALT_LANGUAGES[args.corpus]:
    #     logger.info("Error language/subset setting")
    #     exit()
    # else:
    #     logger.info(dataloader) # drop off languages/subsets with less than 100 instances
    #     try:
    #         if len(dataloader) == 3:
    #             instances = len(dataloader['train']) + len(dataloader['validation']) + len(dataloader['test'])
    #         else:
    #             instances = len(dataloader['test'])
    #     except:
    #         logger.info("Error")
    # if instances < 100:
    #     logger.info(f"{args.lang} has less than 100 instances, drop off from the training process")
    #     exit()

    # wandb init
    project = 'Eval Probing'
    entity = 'yuansui'
    group = 'Paper-revision-layer-wise-and-head-wise'
    display_name = f"fc[{args.fc}]-corpus-[{args.corpus}]-lang-[{args.lang}]-mode[{args.mode}]"
    wandb.init(reinit=True, project=project, entity=entity,
               name=display_name, group=group, tags=["train & eval"])
    wandb.config["args"] = vars(args)

    EvalTrainer(args, dataloader, TAG_DICT_WIKIANN).train(args)


if __name__ == "__main__":
    args = get_arguments()
    main(args)
