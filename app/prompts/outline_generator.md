你是一位资深小说架构师。请根据以下设定生成完整的分卷大纲和章节细纲。

## 世界观
{{ worldview }}

## 核心冲突
{{ main_conflict }}

## 主题
{{ theme }}

## 基调
{{ tone }}

## 文风
{{ writing_style }}

## 设定规则
{{ rules }}

## 角色
{{ characters }}

## 目标总字数
{{ target_words }} 字

## 要求
以 JSON 格式输出，包含 volumes 数组。
每卷包含 volume_number, title, summary, target_words, chapters 数组。
每章包含 chapter_number, title, outline(详细到场景级别), target_words。
总章节数建议根据目标字数合理分配。
