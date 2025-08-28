"""
硅基流动API客户端 - 封装硅基流动API调用
"""
import json
import logging
import os
import re
from typing import Dict, Any, List
from openai import OpenAI
from collections.abc import Generator

from .json_utils import JSONUtils  # 导入统一的JSON工具类

logger = logging.getLogger(__name__)

class SiliconFlowClient:
    """硅基流动API客户端"""
    
    def __init__(self, api_key: str = None, model: str = "Qwen/Qwen2.5-72B-Instruct"):
        """
        初始化硅基流动客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self.model = model
        self.base_url = "https://api.siliconflow.cn/v1"
        
        if not self.api_key:
            raise ValueError("请配置硅基流动API密钥，可以通过环境变量SILICONFLOW_API_KEY或在前端设置页面配置。")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def call(self, prompt: str, input_data: Any = None) -> str:
        """
        调用硅基流动API
        
        Args:
            prompt: 提示词
            input_data: 输入数据
            
        Returns:
            模型响应文本
        """
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
            logger.info(f"🚀 [SiliconFlow调用开始] 模型: {self.model}")
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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'user', 'content': full_input}
                ],
                stream=False
            )
            
            end_time = time.time()
            call_duration = end_time - start_time
            logger.info(f"⏱️ [API调用] 耗时: {call_duration:.2f} 秒")
            
            # 检查响应
            if response and response.choices:
                content = response.choices[0].message.content
                if content:
                    response_length = len(content)
                    finish_reason = response.choices[0].finish_reason if response.choices[0] else 'unknown'
                    
                    logger.info(f"✅ [API调用成功] 响应长度: {response_length} 字符")
                    logger.info(f"🎯 [结束原因]: {finish_reason}")
                    logger.debug(f"📄 [响应内容前500字符]: {content[:500]}...")
                    
                    # 检查响应内容的基本质量
                    if response_length < 10:
                        logger.warning(f"⚠️ [响应质量警告] 响应过短: {response_length} 字符")
                    if '{' in content or '[' in content:
                        logger.info(f"🔍 [响应格式] 检测到JSON格式内容")
                    
                    return content
                else:
                    logger.warning(f"⚠️ [API请求成功，但输出为空] 结束原因: {response.choices[0].finish_reason if response.choices[0] else 'unknown'}")
                    return ""
            else:
                error_msg = "API调用失败，未返回有效响应"
                logger.error(f"❌ [API调用失败] {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            error_type = type(e).__name__
            error_details = str(e)
            logger.error(f"❌ [硅基流动API调用异常] 类型: {error_type}")
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
        logger.info(f"🔄 [SiliconFlow重试机制] 开始调用，最大重试次数: {max_retries}")
        
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
                    logger.error(f"❌ [重试失败] 硅基流动API调用在{max_retries}次重试后彻底失败")
                    logger.error(f"💬 [最终错误] 类型: {error_type}, 信息: {error_msg}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"⚠️ [第{attempt + 1}次失败] 类型: {error_type}, 信息: {error_msg}")
                logger.info(f"⏳ [等待重试] {wait_time}秒后进行第{attempt + 2}次尝试...")
                
                import time
                time.sleep(wait_time)  # 指数退避
                
        return "" # 确保所有路径都有返回值
    
    def parse_json_response(self, response: str) -> Any:
        """
        从可能包含Markdown格式的文本中解析JSON对象。
        使用统一的JSON工具类进行解析和修复。
        """
        return JSONUtils.parse_json_response(response)
    
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
