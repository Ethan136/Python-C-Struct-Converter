"""
v7 解析器實作

提供優化的結構定義解析功能。
"""

import re
from typing import Optional, List
from .ast_node import ASTNode, ASTNodeFactory


class V7StructParser:
    """v7 優化的結構解析器"""
    
    def __init__(self):
        self.node_factory = ASTNodeFactory()
        self.current_id = 0
    
    def parse_struct_definition(self, content: str) -> Optional[ASTNode]:
        """解析結構定義"""
        try:
            # 清理輸入內容
            content = self._clean_content(content)
            
            # 解析結構名稱
            struct_match = re.match(r'struct\s+(\w+)\s*\{', content)
            if not struct_match:
                return None
            
            struct_name = struct_match.group(1)
            root_node = self.node_factory.create_struct_node(struct_name)
            
            # 解析結構體內容
            body_start = content.find('{') + 1
            body_end = self._find_matching_brace(content, body_start - 1)
            if body_end == -1:
                return None
            
            struct_body = content[body_start:body_end]
            
            # 解析成員
            self._parse_members(struct_body, root_node)
            
            return root_node
            
        except Exception as e:
            print(f"解析錯誤: {e}")
            return None

    def _extract_array_dims(self, token: str):
        """回傳變數名稱及陣列維度列表"""
        m = re.match(r"(\w+)((?:\[\d+\])*)", token)
        if not m:
            return token, []
        name = m.group(1)
        dims = [int(n) for n in re.findall(r"\[(\d+)\]", m.group(2))]
        return name, dims
    
    def _parse_members(self, body: str, parent_node: ASTNode):
        """解析結構成員"""
        lines = self._split_member_lines(body)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            member_node = self._parse_member_line(line)
            if member_node:
                parent_node.add_child(member_node)
    
    def _parse_member_line(self, line: str) -> Optional[ASTNode]:
        """解析單一成員行"""
        # 處理巢狀結構
        if line.startswith('struct'):
            return self._parse_nested_struct(line)
        elif line.startswith('union'):
            return self._parse_nested_union(line)
        
        # 處理陣列
        if '[' in line and ']' in line:
            return self._parse_array_member(line)
        
        # 處理位元欄位
        if ':' in line:
            return self._parse_bitfield_member(line)
        
        # 處理基本型別
        return self._parse_basic_member(line)
    
    def _parse_nested_struct(self, line: str) -> Optional[ASTNode]:
        """解析巢狀結構"""
        # 檢查是否為匿名結構
        anonymous_match = re.match(r'struct\s*\{', line)
        if anonymous_match:
            # 匿名結構
            struct_node = self.node_factory.create_struct_node("", is_anonymous=True)
            
            # 提取結構體內容
            body_start = line.find('{') + 1
            body_end = self._find_matching_brace(line, body_start - 1)
            if body_end == -1:
                return None
            
            struct_body = line[body_start:body_end]
            
            # 解析成員
            self._parse_members(struct_body, struct_node)
            
            var_match = re.search(r'\}\s*([^;]+)\s*;', line[body_end:])
            if var_match:
                token = var_match.group(1).strip()
                name, dims = self._extract_array_dims(token)
                struct_node.name = name
                if dims:
                    array_node = self.node_factory.create_array_node(name, "struct", dims)
                    array_node.add_child(struct_node)
                    return array_node

            return struct_node
        else:
            # 有名結構
            struct_match = re.match(r'struct\s+(\w+)\s*\{', line)
            if not struct_match:
                return None
            
            struct_name = struct_match.group(1)
            struct_node = self.node_factory.create_struct_node(struct_name)
            
            # 提取結構體內容
            body_start = line.find('{') + 1
            body_end = self._find_matching_brace(line, body_start - 1)
            if body_end == -1:
                return None
            
            struct_body = line[body_start:body_end]
            
            # 解析成員
            self._parse_members(struct_body, struct_node)
            
            var_match = re.search(r'\}\s*([^;]+)\s*;', line[body_end:])
            if var_match:
                token = var_match.group(1).strip()
                name, dims = self._extract_array_dims(token)
                struct_node.name = name
                if dims:
                    array_node = self.node_factory.create_array_node(name, "struct", dims)
                    array_node.add_child(struct_node)
                    return array_node

            return struct_node
    
    def _parse_nested_union(self, line: str) -> Optional[ASTNode]:
        """解析巢狀聯合"""
        # 檢查是否為匿名聯合
        anonymous_match = re.match(r'union\s*\{', line)
        if anonymous_match:
            # 匿名聯合
            union_node = self.node_factory.create_union_node("", is_anonymous=True)
            
            # 提取聯合體內容
            body_start = line.find('{') + 1
            body_end = self._find_matching_brace(line, body_start - 1)
            if body_end == -1:
                return None
            
            union_body = line[body_start:body_end]
            
            # 解析成員
            self._parse_members(union_body, union_node)
            
            var_match = re.search(r'\}\s*([^;]+)\s*;', line[body_end:])
            if var_match:
                token = var_match.group(1).strip()
                name, dims = self._extract_array_dims(token)
                union_node.name = name
                if dims:
                    array_node = self.node_factory.create_array_node(name, "union", dims)
                    array_node.add_child(union_node)
                    return array_node

            return union_node
        else:
            # 有名聯合
            union_match = re.match(r'union\s+(\w+)\s*\{', line)
            if not union_match:
                return None
            
            union_name = union_match.group(1)
            union_node = self.node_factory.create_union_node(union_name)
            
            # 提取聯合體內容
            body_start = line.find('{') + 1
            body_end = self._find_matching_brace(line, body_start - 1)
            if body_end == -1:
                return None
            
            union_body = line[body_start:body_end]
            
            # 解析成員
            self._parse_members(union_body, union_node)
            
            var_match = re.search(r'\}\s*([^;]+)\s*;', line[body_end:])
            if var_match:
                token = var_match.group(1).strip()
                name, dims = self._extract_array_dims(token)
                union_node.name = name
                if dims:
                    array_node = self.node_factory.create_array_node(name, "union", dims)
                    array_node.add_child(union_node)
                    return array_node

            return union_node
    
    def _parse_array_member(self, line: str) -> Optional[ASTNode]:
        """解析陣列成員"""
        # 提取型別和名稱
        type_name_match = re.match(r'(\w+(?:\s+\w+)*)\s+(\w+)\s*\[', line)
        if not type_name_match:
            return None
        
        type_name = type_name_match.group(1).strip()
        var_name = type_name_match.group(2)
        
        # 提取陣列維度
        dimensions = []
        dim_pattern = r'\[(\d+)\]'
        for match in re.finditer(dim_pattern, line):
            dimensions.append(int(match.group(1)))
        
        if not dimensions:
            return None
        
        # 建立陣列節點
        array_node = self.node_factory.create_array_node(var_name, type_name, dimensions)
        
        return array_node
    
    def _parse_bitfield_member(self, line: str) -> Optional[ASTNode]:
        """解析位元欄位成員（型別關鍵字判斷，最穩健方案）"""
        import re
        c_types = {'char', 'short', 'int', 'long', 'float', 'double', 'unsigned', 'signed', 'struct', 'union', 'enum', 'bool'}
        m = re.match(r'^(.*)\s*:\s*(\d+)\s*;$', line.strip())
        if m:
            before = m.group(1).strip()
            bit_size = int(m.group(2))
            parts = before.split()
            if len(parts) == 1 or parts[-1] in c_types:
                # 匿名 bitfield
                type_name = before
                node = self.node_factory.create_bitfield_node("", type_name, bit_size)
                node.is_anonymous = True
                return node
            else:
                # 有名 bitfield
                type_name = ' '.join(parts[:-1])
                var_name = parts[-1]
                return self.node_factory.create_bitfield_node(var_name, type_name, bit_size)
        return None
    
    def _parse_basic_member(self, line: str) -> Optional[ASTNode]:
        """解析基本型別成員"""
        # 提取型別和名稱
        member_pattern = r'(\w+(?:\s+\w+)*)\s+(\w+)\s*;'
        match = re.match(member_pattern, line)
        if not match:
            return None
        
        type_name = match.group(1).strip()
        var_name = match.group(2)
        
        # 建立基本型別節點
        basic_node = self.node_factory.create_basic_node(var_name, type_name)
        
        return basic_node
    
    def _clean_content(self, content: str) -> str:
        """清理輸入內容"""
        # 移除註解
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # 移除多餘空白
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _find_matching_brace(self, content: str, start: int) -> int:
        """尋找匹配的大括號"""
        brace_count = 0
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i
        return -1
    
    def _split_member_lines(self, body: str) -> List[str]:
        """語意切分 struct/union 成員，正確處理匿名 bitfield"""
        import re
        lines = []
        current_line = ""
        brace_count = 0
        for char in body:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            if char == ';' and brace_count == 0:
                current_line += char
                lines.append(current_line.strip())
                current_line = ""
                continue
            current_line += char
        if current_line.strip():
            lines.append(current_line.strip())
        # 合併只有 ': ... ;' 的片段到上一行，去除上一行分號並 strip
        merged_lines = []
        for line in lines:
            if re.match(r'^:\s*\d+\s*;$', line) and merged_lines:
                merged_lines[-1] = re.sub(r';\s*$', '', merged_lines[-1]) + line
                merged_lines[-1] = merged_lines[-1].strip()
            else:
                merged_lines.append(line)
        # Debug output removed or guarded for production use
        # print("[DEBUG] merged_lines:", merged_lines)
        return merged_lines 