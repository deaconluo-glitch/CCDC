import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import streamlit as st

class ComplaintDatabase:
    def __init__(self):
        # Supabase配置 (从环境变量或Streamlit secrets获取)
        try:
            self.supabase_url = st.secrets["supabase"]["url"]
            self.supabase_key = st.secrets["supabase"]["key"]
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        except:
            # 本地开发时使用模拟数据
            self.supabase = None
            st.warning("Supabase配置未找到，使用模拟数据模式")
    
    def create_tables(self):
        """创建数据库表结构"""
        # 在实际使用中，这里应该是SQL创建语句
        # 现在先用DataFrame模拟
        return True
    
    def upload_complaint_data(self, df, table_name="complaints"):
        """上传客诉数据到数据库"""
        if self.supabase:
            try:
                # 转换为字典列表格式
                records = df.to_dict('records')
                response = self.supabase.table(table_name).insert(records).execute()
                return True, f"成功上传 {len(records)} 条记录"
            except Exception as e:
                return False, str(e)
        else:
            # 模拟模式
            st.session_state[f"{table_name}_data"] = df
            return True, f"模拟上传 {len(df)} 条记录到 {table_name}"
    
    def upload_shipment_data(self, df, table_name="shipments"):
        """上传出货数据到数据库"""
        return self.upload_complaint_data(df, table_name)
    
    def upload_sn_database(self, df_a, df_b=None):
        """上传SN数据库"""
        if self.supabase:
            # 上传数据库A
            if df_a is not None:
                records_a = df_a.to_dict('records')
                self.supabase.table("sn_database_a").insert(records_a).execute()
            
            # 上传数据库B (微逆)
            if df_b is not None:
                records_b = df_b.to_dict('records')
                self.supabase.table("sn_database_b").insert(records_b).execute()
            return True, "SN数据库上传成功"
        else:
            # 模拟模式
            st.session_state["sn_database_a"] = df_a
            if df_b is not None:
                st.session_state["sn_database_b"] = df_b
            return True, "SN数据库模拟上传成功"
    
    def get_complaint_data(self, start_date=None, end_date=None, machine_type=None):
        """获取客诉数据"""
        if self.supabase:
            query = self.supabase.table("complaints").select("*")
            
            if start_date:
                query = query.gte("complain_date", start_date)
            if end_date:
                query = query.lte("complain_date", end_date)
            if machine_type:
                query = query.eq("machine_type_std", machine_type)
                
            response = query.execute()
            return pd.DataFrame(response.data)
        else:
            # 模拟模式
            return st.session_state.get("complaints_data", pd.DataFrame())
    
    def get_shipment_data(self, start_date=None, end_date=None, machine_type=None):
        """获取出货数据"""
        if self.supabase:
            query = self.supabase.table("shipments").select("*")
            
            if start_date:
                query = query.gte("shipment_date", start_date)
            if end_date:
                query = query.lte("shipment_date", end_date)
            if machine_type:
                query = query.eq("machine_type_std", machine_type)
                
            response = query.execute()
            return pd.DataFrame(response.data)
        else:
            # 模拟模式
            return st.session_state.get("shipments_data", pd.DataFrame())
