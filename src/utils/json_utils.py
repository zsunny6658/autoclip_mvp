"""
JSON工具类 - 提供统一的JSON解析和修复功能
"""
import json
import logging
import re
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

class JSONUtils:
    """JSON工具类"""
    
    @staticmethod
    def sanitize_string(s: str) -> str:
        """增强的净化函数，移除可能导致JSON解析失败的字符"""
        # 移除BOM标记
        s = s.lstrip('\ufeff')
        # 移除前后空白符
        s = s.strip()
        # 移除可能的控制字符（保留必要的换行和制表符）
        s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
        return s
    
    @staticmethod
    def fix_common_json_errors(json_str: str) -> str:
        """修复常见的JSON格式错误"""
        # 记录原始字符串用于调试
        original_str = json_str
        
        # 1. 修复缺少逗号的问题
        json_str = re.sub(r'}\s*{', '},{', json_str)
        json_str = re.sub(r']\s*\[', '],[', json_str)
        
        # 2. 修复对象之间缺少逗号的问题（更精确的模式）
        json_str = re.sub(r'}\s*\n\s*{', '},\n{', json_str)
        
        # 3. 修复多余的逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 4. 修复单引号为双引号
        json_str = re.sub(r"'([^']*?)'\s*:", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*?)'", r': "\1"', json_str)
        
        # 5. 修复字段名没有引号的问题
        json_str = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', json_str)
        
        # 6. 修复可能的换行符问题
        json_str = re.sub(r'\n\s*\n', '\n', json_str)
        
        # 7. 修复双反斜杠转义的引号问题 (\\\" -> \")
        json_str = re.sub(r'\\\\\\"', r'\\"', json_str)
        
        # 8. 修复字段名拼写错误（如conten -> content）
        json_str = re.sub(r'"conten"\s*:', r'"content":', json_str)
        
        # 9. 确保数组和对象的正确闭合
        # 统计括号和方括号的数量
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # 如果括号不匹配，尝试修复
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        
        # 记录修复过程
        if json_str != original_str:
            logger.debug(f"JSON修复前: {original_str[:100]}...")
            logger.debug(f"JSON修复后: {json_str[:100]}...")
        
        return json_str
    
    @staticmethod
    def fix_truncated_json(json_str: str) -> str:
        """尝试修复被截断的JSON字符串"""
        if not json_str:
            return json_str
            
        # 如果以...结尾，移除...
        if json_str.endswith('...'):
            json_str = json_str[:-3]
            
        # 尝试修复常见的截断问题
        # 修复字段名拼写错误（如conten... -> content）
        json_str = re.sub(r'"conten\.\.\."', r'"content"', json_str)
        
        # 修复未闭合的字符串
        if json_str.count('"') % 2 == 1:  # 奇数个引号，说明有一个未闭合
            # 找到最后一个未闭合的引号位置
            last_quote = json_str.rfind('"')
            if last_quote >= 0:
                # 检查引号后是否有未闭合的内容
                after_quote = json_str[last_quote+1:]
                if after_quote and not after_quote.isspace():
                    # 如果引号后有内容但没有闭合引号，添加闭合引号
                    json_str = json_str[:last_quote+1] + '"' + json_str[last_quote+1:]
        
        # 尝试补全JSON结构
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # 补全缺失的闭合符号
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
            
        # 确保以闭合符号结尾
        if json_str and json_str[-1] not in ['}', ']']:
            # 找到最后一个闭合符号的位置
            last_brace = json_str.rfind('}')
            last_bracket = json_str.rfind(']')
            last_close = max(last_brace, last_bracket)
            
            if last_close >= 0:
                # 截断到最近的闭合符号
                json_str = json_str[:last_close+1]
            
        return json_str

    @staticmethod
    def preprocess_llm_response(response: str) -> str:
        """预处理LLM响应，移除常见的非JSON内容"""
        # 移除开头的标题和说明文字
        lines = response.split('\n')
        json_start = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('[') or stripped.startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            response = '\n'.join(lines[json_start:])
        
        # 移除末尾的非JSON内容
        if '```' in response:
            # 如果有多个```，取第一个之前的内容
            parts = response.split('```')
            if len(parts) > 1:
                response = parts[0]
        
        return response.strip()
    
    @staticmethod
    def parse_json_response(response: str) -> Any:
        """
        从可能包含Markdown格式的文本中解析JSON对象。
        该函数具有多层容错机制：
        1. 预处理响应，移除非JSON内容
        2. 优先从Markdown代码块提取。
        3. 如果失败，则尝试直接解析整个响应（在净化后）。
        4. 如果再次失败，则使用通用正则表达式寻找并解析JSON。
        5. 最后尝试修复常见JSON错误后再解析。
        6. 对于被截断的JSON，尝试修复后再解析。
        """
        
        logger.info(f"🔍 [JSON解析开始] 原始响应长度: {len(response)} 字符")
        logger.debug(f"📄 [原始响应前300字符]: {response[:300]}...")
        
        response = response.strip()
        
        # 0. 预处理响应，移除非JSON内容
        response = JSONUtils.preprocess_llm_response(response)
        logger.info(f"🧹 [预处理完成] 处理后长度: {len(response)} 字符")
        logger.debug(f"📄 [预处理后内容前200字符]: {response[:200]}...")
        
        # 特殊处理被截断的JSON（以...结尾的情况）
        if response.endswith('...') and (response.startswith('[') or response.startswith('{')):
            logger.info("🔍 [检测到被截断的JSON] 尝试修复...")
            response = JSONUtils.fix_truncated_json(response)
            logger.info(f"🔧 [修复后长度]: {len(response)} 字符")
            logger.debug(f"📄 [修复后内容]: {response[:200]}...")
        
        # 1. 优先尝试从Markdown代码块中提取
        logger.info(f"🔍 [阶段1] 尝试从Markdown代码块提取JSON...")
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response, re.DOTALL)
        if match:
            json_str = JSONUtils.sanitize_string(match.group(1))
            logger.info(f"✅ [Markdown提取成功] JSON字符串长度: {len(json_str)}")
            logger.debug(f"📄 [Markdown提取内容]: {json_str[:200]}...")
            try:
                result = json.loads(json_str)
                logger.info(f"✅ [阶段1成功] Markdown提取并解析JSON成功")
                return result
            except json.JSONDecodeError as e:
                # 记录具体的错误位置和上下文
                error_pos = e.pos if hasattr(e, 'pos') else 0
                context_start = max(0, error_pos - 50)
                context_end = min(len(json_str), error_pos + 50)
                context = json_str[context_start:context_end]
                logger.error(f"❌ [JSON解析失败] 位置{error_pos}，上下文: ...{context}...")
                logger.warning(f"⚠️ [阶段1失败] 从Markdown提取的内容解析失败: {e}。将尝试修复后解析。")
                
                # 尝试修复常见错误后再解析
                try:
                    logger.info(f"🔧 [尝试修复] 修复JSON格式错误...")
                    fixed_json = JSONUtils.fix_common_json_errors(json_str)
                    result = json.loads(fixed_json)
                    logger.info(f"✅ [阶段1修复成功] JSON修复后解析成功")
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ [修复失败] 修复后仍然解析失败，将尝试解析整个响应。")
        else:
            logger.info(f"💫 [阶段1跳过] 未找到Markdown代码块")
        
        # 2. 如果没有Markdown，或Markdown解析失败，尝试整个响应
        logger.info(f"🔍 [阶段2] 尝试直接解析整个响应...")
        try:
            sanitized_response = JSONUtils.sanitize_string(response)
            logger.debug(f"🧹 [净化后内容]: {sanitized_response[:200]}...")
            result = json.loads(sanitized_response)
            logger.info(f"✅ [阶段2成功] 直接解析整个响应成功")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ [阶段2失败] 直接解析响应失败: {e}")
            
            # 3. 如果整个响应直接解析也失败，做最后一次尝试，用通用正则寻找
            logger.info(f"🔍 [阶段3] 使用通用正则表达式寻找JSON...")
            json_match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', response, re.DOTALL)
            if json_match:
                json_str = JSONUtils.sanitize_string(json_match.group())
                logger.info(f"✅ [正则匹配成功] 找到JSON结构，长度: {len(json_str)}")
                logger.debug(f"📄 [正则匹配内容]: {json_str[:200]}...")
                try:
                    result = json.loads(json_str)
                    logger.info(f"✅ [阶段3成功] 正则匹配并解析JSON成功")
                    return result
                except json.JSONDecodeError as e:
                    # 4. 最后尝试修复常见错误
                    logger.warning(f"⚠️ [阶段3失败] 正则匹配内容解析失败: {e}")
                    try:
                        logger.info(f"🔧 [最后尝试] 修复JSON后再次解析...")
                        fixed_json = JSONUtils.fix_common_json_errors(json_str)
                        result = json.loads(fixed_json)
                        logger.info(f"✅ [最终成功] JSON修复后解析成功")
                        return result
                    except json.JSONDecodeError as final_e:
                        logger.error(f"❌ [最终失败] 所有尝试都失败: {final_e}")
                        # 保存原始响应以便调试
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                            f.write(response)
                            logger.error(f"💾 [调试信息] 原始响应已保存到 {f.name} 以便调试")
                        raise ValueError(f"无法从响应中解析出有效的JSON: {response[:200]}...") from final_e
            else:
                logger.error(f"❌ [正则匹配失败] 未找到任何JSON结构")
            
            # 如果连通用正则都找不到，就彻底失败
            logger.error(f"❌ [彻底失败] 所有JSON解析方法都失败")
            raise ValueError(f"无法从响应中解析出有效的JSON: {response[:200]}...")