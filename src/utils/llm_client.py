"""
大模型客户端 - 封装通义千问API调用
"""
import json
import logging
import os
import re
from typing import Dict, Any, List
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse
from collections.abc import Generator

from ..config import MODEL_NAME

logger = logging.getLogger(__name__)

class LLMClient:
    """通义千问API客户端"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        初始化通义千问客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            model: 模型名称，如果为None则使用默认模型
        """
        self.model = model or MODEL_NAME
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    
    def call(self, prompt: str, input_data: Any = None) -> str:
        """
        调用大模型API
        
        Args:
            prompt: 提示词
            input_data: 输入数据
            
        Returns:
            模型响应文本
        """
        api_key = self.api_key
        if not api_key:
            raise ValueError("请配置API密钥，可以通过环境变量DASHSCOPE_API_KEY或在前端设置页面配置。")

        try:
            # 构建完整的输入
            if input_data:
                if isinstance(input_data, dict):
                    full_input = f"{prompt}\n\n输入内容：\n{json.dumps(input_data, ensure_ascii=False, indent=2)}"
                else:
                    full_input = f"{prompt}\n\n输入内容：\n{input_data}"
            else:
                full_input = prompt
            
            # 记录调用开始的详细信息
            logger.info(f"🚀 [LLM调用开始] 模型: {self.model}")
            logger.info(f"📝 [提示词长度]: {len(prompt)} 字符")
            if input_data:
                input_type = type(input_data).__name__
                if isinstance(input_data, (dict, list)):
                    input_size = len(json.dumps(input_data, ensure_ascii=False))
                    logger.info(f"📊 [输入数据]: 类型={input_type}, 大小={input_size} 字符")
                else:
                    logger.info(f"📊 [输入数据]: 类型={input_type}, 长度={len(str(input_data))} 字符")
            logger.info(f"🔢 [完整输入长度]: {len(full_input)} 字符")
            logger.debug(f"📄 [完整输入内容前500字符]: {full_input[:500]}...")
            
            # 调用API
            import time
            start_time = time.time()
            logger.info(f"⏱️ [API调用] 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            response_or_gen = Generation.call(
                model=self.model,
                prompt=full_input,
                api_key=api_key,
                stream=False, # 确保使用非流式调用
            )
            
            end_time = time.time()
            call_duration = end_time - start_time
            logger.info(f"⏱️ [API调用] 耗时: {call_duration:.2f} 秒")
            
            response: GenerationResponse
            if isinstance(response_or_gen, Generator):
                response = next(response_or_gen)
            else:
                response = response_or_gen

            # 详细检查API响应
            logger.info(f"📥 [API响应] 状态码: {response.status_code if response else 'None'}")
            
            if response and response.status_code == 200:
                if response.output and response.output.text is not None:
                    response_text = response.output.text
                    response_length = len(response_text)
                    finish_reason = response.output.finish_reason if response.output else 'unknown'
                    
                    logger.info(f"✅ [API调用成功] 响应长度: {response_length} 字符")
                    logger.info(f"🎯 [结束原因]: {finish_reason}")
                    logger.debug(f"📄 [响应内容前500字符]: {response_text[:500]}...")
                    
                    # 检查响应内容的基本质量
                    if response_length < 10:
                        logger.warning(f"⚠️ [响应质量警告] 响应过短: {response_length} 字符")
                    if '{' in response_text or '[' in response_text:
                        logger.info(f"🔍 [响应格式] 检测到JSON格式内容")
                    
                    return response_text
                else:
                    # API成功但输出为空，可能是内容安全过滤等原因
                    finish_reason = response.output.finish_reason if response.output else 'unknown'
                    usage_info = f"输入tokens: {response.usage.input_tokens if response.usage else 'N/A'}, 输出tokens: {response.usage.output_tokens if response.usage else 'N/A'}" if hasattr(response, 'usage') and response.usage else "使用量信息不可用"
                    
                    error_msg = f"API请求成功，但输出为空。结束原因: {finish_reason}, 使用量: {usage_info}"
                    logger.warning(f"⚠️ [输出为空] {error_msg}")
                    return "" # 返回空字符串，让上层处理
            else:
                # API调用失败
                code = response.code if hasattr(response, 'code') else 'N/A'
                message = response.message if hasattr(response, 'message') else '未知API错误'
                status_code = response.status_code if response else 'N/A'
                
                logger.error(f"❌ [API调用失败] 状态码: {status_code}, 错误码: {code}")
                logger.error(f"💬 [错误信息]: {message}")
                
                if "Invalid ApiKey" in str(message):
                    logger.error(f"🔑 [API Key错误] 请检查配置的API密钥是否正确")
                    raise ValueError("API Key无效或不正确，请检查配置并重新输入。")

                error_msg = f"API调用失败 - Status: {status_code}, Code: {code}, Message: {message}"
                raise Exception(message)
                
        except StopIteration:
            # next(response_gen) 可能会在生成器为空时引发此异常
            error_msg = "API调用未返回任何响应。"
            logger.error(f"❌ [StopIteration错误] {error_msg}")
            logger.error(f"📄 [调用上下文] 模型: {self.model}, 输入长度: {len(full_input)}")
            raise Exception(error_msg)
        except Exception as e:
            error_type = type(e).__name__
            error_details = str(e)
            logger.error(f"❌ [LLM调用异常] 类型: {error_type}")
            logger.error(f"💬 [异常详情]: {error_details}")
            logger.error(f"📄 [调用上下文] 模型: {self.model}, 输入长度: {len(full_input) if 'full_input' in locals() else 'N/A'}")
            raise
    
    def call_with_retry(self, prompt: str, input_data: Any = None, max_retries: int = 3) -> str:
        """
        带重试机制的API调用
        
        Args:
            prompt: 提示词
            input_data: 输入数据
            max_retries: 最大重试次数
            
        Returns:
            模型响应文本
        """
        logger.info(f"🔄 [重试机制] 开始调用，最大重试次数: {max_retries}")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔢 [第{attempt + 1}次尝试] 开始调用...")
                result = self.call(prompt, input_data)
                logger.info(f"✅ [第{attempt + 1}次尝试成功] 调用完成")
                return result
            except ValueError as ve: # 如果是API Key或参数错误，不重试
                logger.error(f"❌ [不可重试错误] {str(ve)}")
                raise
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                if attempt == max_retries - 1:
                    logger.error(f"❌ [重试失败] LLM调用在{max_retries}次重试后彻底失败")
                    logger.error(f"💬 [最终错误] 类型: {error_type}, 信息: {error_msg}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"⚠️ [第{attempt + 1}次失败] 类型: {error_type}, 信息: {error_msg}")
                logger.info(f"⏳ [等待重试] {wait_time}秒后进行第{attempt + 2}次尝试...")
                
                import time
                time.sleep(wait_time)  # 指数退避
                
        return "" # 确保所有路径都有返回值
    
    def _preprocess_llm_response(self, response: str) -> str:
        """
        预处理LLM响应，移除常见的非JSON内容
        """
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
    
    def _auto_fix_response(self, response: str) -> str:
        """
        自动修复常见的响应问题
        """
        # 移除BOM和特殊字符
        response = response.lstrip('\ufeff')
        response = response.strip()
        
        # 修复中文引号
        response = response.replace('"', '\"').replace('"', '\"')
        
        return response
    
    def _validate_json_structure(self, parsed_data: Any) -> bool:
        """
        验证JSON结构的有效性
        """
        try:
            if not isinstance(parsed_data, list):
                logger.error(f"响应不是数组格式，实际类型: {type(parsed_data)}")
                return False
            
            for i, item in enumerate(parsed_data):
                if not isinstance(item, dict):
                    logger.error(f"第{i}个元素不是对象格式，实际类型: {type(item)}")
                    return False
                    
                # 检查基本字段（可根据具体需求调整）
                if 'outline' in item or 'start_time' in item or 'end_time' in item:
                    required_fields = ['outline', 'start_time', 'end_time']
                    for field in required_fields:
                        if field not in item:
                            logger.error(f"第{i}个元素缺少必需字段: {field}")
                            return False
        except Exception as e:
            logger.error(f"验证JSON结构时出错: {e}")
            return False
        
        return True
    
    def parse_json_response(self, response: str) -> Any:
        """
        从可能包含Markdown格式的文本中解析JSON对象。
        该函数具有多层容错机制：
        1. 预处理响应，移除非JSON内容
        2. 优先从Markdown代码块提取。
        3. 如果失败，则尝试直接解析整个响应（在净化后）。
        4. 如果再次失败，则使用通用正则表达式寻找并解析JSON。
        5. 最后尝试修复常见JSON错误后再解析。
        """
        
        logger.info(f"🔍 [JSON解析开始] 原始响应长度: {len(response)} 字符")
        logger.debug(f"📄 [原始响应前300字符]: {response[:300]}...")
        
        def sanitize_string(s: str) -> str:
            """增强的净化函数，移除可能导致JSON解析失败的字符"""
            # 移除BOM标记
            s = s.lstrip('\ufeff')
            # 移除前后空白符
            s = s.strip()
            # 移除可能的控制字符（保留必要的换行和制表符）
            s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
            return s
        
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
            
            # 7. 确保数组和对象的正确闭合
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

        response = response.strip()
        
        # 0. 预处理响应，移除非JSON内容
        response = self._preprocess_llm_response(response)
        logger.info(f"🧹 [预处理完成] 处理后长度: {len(response)} 字符")
        logger.debug(f"📄 [预处理后内容前200字符]: {response[:200]}...")
        
        # 1. 优先尝试从Markdown代码块中提取
        logger.info(f"🔍 [阶段1] 尝试从Markdown代码块提取JSON...")
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response, re.DOTALL)
        if match:
            json_str = sanitize_string(match.group(1))
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
                    fixed_json = fix_common_json_errors(json_str)
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
            sanitized_response = sanitize_string(response)
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
                json_str = sanitize_string(json_match.group())
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
                        fixed_json = fix_common_json_errors(json_str)
                        result = json.loads(fixed_json)
                        logger.info(f"✅ [最终成功] JSON修复后解析成功")
                        return result
                    except json.JSONDecodeError as final_e:
                        logger.error(f"❌ [最终失败] 所有尝试都失败: {final_e}")
                        # 保存原始响应以便调试
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                            f.write(response)
                            logger.error(f"💾 [调试信息] 原始响应已保存到 {f.name} 以便调试")
                        raise ValueError(f"无法从响应中解析出有效的JSON: {response[:200]}...") from final_e
            else:
                logger.error(f"❌ [正则匹配失败] 未找到任何JSON结构")
            
            # 如果连通用正则都找不到，就彻底失败
            logger.error(f"❌ [彻底失败] 所有JSON解析方法都失败")
            raise ValueError(f"无法从响应中解析出有效的JSON: {response[:200]}...")