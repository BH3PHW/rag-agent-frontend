"""
数据转换和预处理模块
将各电商平台的不同数据格式统一转换为系统内部格式
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from .ecommerce_platforms import (
    PlatformType,
    OrderInfo,
    ProductInfo
)


class OrderStatus(Enum):
    """统一订单状态枚举"""
    PENDING = "待付款"
    PAID = "已付款"
    PROCESSING = "处理中"
    SHIPPED = "已发货"
    DELIVERED = "已签收"
    CANCELLED = "已取消"
    REFUNDED = "已退款"


class BaseDataTransformer:
    """数据转换器基类"""
    
    def transform_order(self, raw_order: Dict[str, Any]) -> OrderInfo:
        """转换平台原始订单数据为统一格式"""
        raise NotImplementedError
    
    def transform_product(self, raw_product: Dict[str, Any]) -> ProductInfo:
        """转换平台原始商品数据为统一格式"""
        raise NotImplementedError
    
    def transform_order_list(self, raw_orders: List[Dict[str, Any]]) -> List[OrderInfo]:
        """批量转换订单列表"""
        return [self.transform_order(order) for order in raw_orders]
    
    def transform_product_list(self, raw_products: List[Dict[str, Any]]) -> List[ProductInfo]:
        """批量转换商品列表"""
        return [self.transform_product(product) for product in raw_products]


class TaobaoDataTransformer(BaseDataTransformer):
    """淘宝/天猫数据转换器"""
    
    ORDER_STATUS_MAP = {
        "WAIT_BUYER_PAY": OrderStatus.PENDING,
        "WAIT_SELLER_SEND_GOODS": OrderStatus.PAID,
        "WAIT_BUYER_CONFIRM_GOODS": OrderStatus.SHIPPED,
        "TRADE_FINISHED": OrderStatus.DELIVERED,
        "TRADE_CLOSED": OrderStatus.CANCELLED
    }
    
    def transform_order(self, raw_order: Dict[str, Any]) -> OrderInfo:
        """转换淘宝订单数据"""
        # 提取字段并处理
        status_str = raw_order.get("status", "")
        order_status = self.ORDER_STATUS_MAP.get(status_str, OrderStatus.PENDING)
        
        # 处理时间字段
        created_at = self._parse_time(raw_order.get("created"))
        paid_at = self._parse_time(raw_order.get("pay_time"))
        shipped_at = self._parse_time(raw_order.get("consign_time"))
        
        # 处理订单金额
        total_amount = float(raw_order.get("payment", 0))
        
        # 处理商品列表
        items = self._extract_items(raw_order)
        
        # 处理收货地址
        shipping_address = raw_order.get("receiver_name", "")
        if raw_order.get("receiver_state"):
            shipping_address = f"{raw_order.get('receiver_state', '')}{raw_order.get('receiver_city', '')}{raw_order.get('receiver_district', '')}{raw_order.get('receiver_address', '')}"
        
        return OrderInfo(
            order_id=f"tb_{raw_order.get('tid', '')}",
            platform_order_id=str(raw_order.get('tid', '')),
            platform=PlatformType.TAOBAO,
            buyer_name=raw_order.get("buyer_nick", ""),
            buyer_phone=raw_order.get("receiver_mobile"),
            order_status=order_status.value,
            order_amount=total_amount,
            shipping_address=shipping_address,
            items=items,
            created_at=created_at,
            paid_at=paid_at,
            shipped_at=shipped_at,
            shipping_tracking_number=raw_order.get("tid"),
            shipping_carrier=raw_order.get("company_name"),
            extra_info={
                "trade_status": status_str,
                "buyer_rate": raw_order.get("buyer_rate"),
                "seller_rate": raw_order.get("seller_rate"),
                "adjust_fee": raw_order.get("adjust_fee"),
                "post_fee": raw_order.get("post_fee")
            }
        )
    
    def transform_product(self, raw_product: Dict[str, Any]) -> ProductInfo:
        """转换淘宝商品数据"""
        return ProductInfo(
            product_id=f"tb_{raw_product.get('num_iid', '')}",
            platform_product_id=str(raw_product.get('num_iid', '')),
            platform=PlatformType.TAOBAO,
            title=raw_product.get("title", ""),
            price=float(raw_product.get("price", 0)),
            stock=int(raw_product.get("num", 0)),
            sku=raw_product.get("sku_id"),
            description=raw_product.get("sub_title", ""),
            images=[raw_product.get("pic_url", "")] if raw_product.get("pic_url") else [],
            category=raw_product.get("cid", ""),
            is_on_sale=raw_product.get("approve_status", "") == "onsale",
            extra_info={
                "price": raw_product.get("price"),
                "old_price": raw_product.get("old_price"),
                "props": raw_product.get("props")
            }
        )
    
    def _extract_items(self, raw_order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从订单中提取商品项"""
        orders = raw_order.get("orders", [])
        items = []
        for order in orders:
            items.append({
                "title": order.get("title", ""),
                "price": float(order.get("price", 0)),
                "quantity": int(order.get("num", 0)),
                "sku_id": order.get("oid"),
                "pic_path": order.get("pic_path", ""),
                "item_url": order.get("item_url", "")
            })
        return items
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except:
            return None


class JDDDataTransformer(BaseDataTransformer):
    """京东数据转换器"""
    
    ORDER_STATUS_MAP = {
        "WAIT_PAY": OrderStatus.PENDING,
        "PAID": OrderStatus.PAID,
        "WAIT_SELLER_DELIVERY": OrderStatus.PROCESSING,
        "DELIVERED": OrderStatus.SHIPPED,
        "FINISHED": OrderStatus.DELIVERED,
        "CANCELED": OrderStatus.CANCELLED
    }
    
    def transform_order(self, raw_order: Dict[str, Any]) -> OrderInfo:
        """转换京东订单数据"""
        status_str = raw_order.get("order_state", "")
        order_status = self.ORDER_STATUS_MAP.get(status_str, OrderStatus.PENDING)
        
        return OrderInfo(
            order_id=f"jd_{raw_order.get('order_id', '')}",
            platform_order_id=str(raw_order.get('order_id', '')),
            platform=PlatformType.JD,
            buyer_name=raw_order.get("consignee_name", ""),
            buyer_phone=raw_order.get("consignee_phone"),
            order_status=order_status.value,
            order_amount=float(raw_order.get("order_price", 0)),
            shipping_address=raw_order.get("full_address", ""),
            items=self._extract_items(raw_order),
            created_at=self._parse_time(raw_order.get("order_start_time")),
            paid_at=self._parse_time(raw_order.get("payment_time")),
            shipped_at=self._parse_time(raw_order.get("delivery_time")),
            shipping_tracking_number=raw_order.get("waybill"),
            shipping_carrier=raw_order.get("logistics_name"),
            extra_info={
                "order_state": status_str,
                "freight_price": raw_order.get("freight_price"),
                "coupon_price": raw_order.get("coupon_price")
            }
        )
    
    def transform_product(self, raw_product: Dict[str, Any]) -> ProductInfo:
        """转换京东商品数据"""
        return ProductInfo(
            product_id=f"jd_{raw_product.get('sku_id', '')}",
            platform_product_id=str(raw_product.get('sku_id', '')),
            platform=PlatformType.JD,
            title=raw_product.get("name", ""),
            price=float(raw_product.get("price", 0)),
            stock=int(raw_product.get("stock_num", 0)),
            sku=str(raw_product.get("sku_id", "")),
            description=raw_product.get("introduction", ""),
            images=raw_product.get("image_list", []),
            category=str(raw_product.get("category_id", "")),
            is_on_sale=raw_product.get("status", 1) == 1,
            extra_info={
                "brand": raw_product.get("brand_name"),
                "upc": raw_product.get("upc"),
                "isbn": raw_product.get("isbn")
            }
        )
    
    def _extract_items(self, raw_order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取订单商品项"""
        items = raw_order.get("item_list", [])
        return [
            {
                "title": item.get("name", ""),
                "price": float(item.get("price", 0)),
                "quantity": int(item.get("item_total", 0)),
                "sku_id": item.get("item_id"),
                "pic_path": item.get("item_img", "")
            }
            for item in items
        ]
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
            except:
                return None


class PinduoduoDataTransformer(BaseDataTransformer):
    """拼多多数据转换器"""
    
    ORDER_STATUS_MAP = {
        0: OrderStatus.PENDING,
        1: OrderStatus.PAID,
        2: OrderStatus.SHIPPED,
        3: OrderStatus.DELIVERED,
        5: OrderStatus.CANCELLED,
        10: OrderStatus.REFUNDED
    }
    
    def transform_order(self, raw_order: Dict[str, Any]) -> OrderInfo:
        """转换拼多多订单数据"""
        status_code = raw_order.get("order_status", 0)
        order_status = self.ORDER_STATUS_MAP.get(status_code, OrderStatus.PENDING)
        
        return OrderInfo(
            order_id=f"pdd_{raw_order.get('order_sn', '')}",
            platform_order_id=str(raw_order.get('order_sn', '')),
            platform=PlatformType.PINDUODUO,
            buyer_name=raw_order.get("receiver_name", ""),
            buyer_phone=raw_order.get("receiver_phone"),
            order_status=order_status.value,
            order_amount=float(raw_order.get("order_amount", 0)),
            shipping_address=raw_order.get("address", ""),
            items=self._extract_items(raw_order),
            created_at=self._parse_time(raw_order.get("order_create_time")),
            paid_at=self._parse_time(raw_order.get("order_pay_time")),
            shipped_at=self._parse_time(raw_order.get("shipping_time")),
            shipping_tracking_number=raw_order.get("tracking_number"),
            shipping_carrier=raw_order.get("shipping_name"),
            extra_info={
                "group_id": raw_order.get("group_order_id"),
                "refund_status": raw_order.get("after_sales_status")
            }
        )
    
    def transform_product(self, raw_product: Dict[str, Any]) -> ProductInfo:
        """转换拼多多商品数据"""
        return ProductInfo(
            product_id=f"pdd_{raw_product.get('goods_id', '')}",
            platform_product_id=str(raw_product.get('goods_id', '')),
            platform=PlatformType.PINDUODUO,
            title=raw_product.get("goods_name", ""),
            price=float(raw_product.get("min_group_price", 0)) / 100,
            stock=int(raw_product.get("goods_quantity", 0)),
            sku=str(raw_product.get("sku_id", "")),
            description=raw_product.get("goods_desc", ""),
            images=raw_product.get("goods_gallery_urls", []),
            category=str(raw_product.get("cat_id", "")),
            is_on_sale=raw_product.get("is_onsale", True),
            extra_info={
                "sold_quantity": raw_product.get("sold_quantity"),
                "goods_type": raw_product.get("goods_type")
            }
        )
    
    def _extract_items(self, raw_order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取订单商品"""
        items = []
        # 拼多多通常是单个商品订单
        items.append({
            "title": raw_product.get("goods_name", ""),
            "price": float(raw_product.get("goods_price", 0)),
            "quantity": 1,
            "sku_id": raw_product.get("sku_id")
        })
        return items
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间戳"""
        if not time_str:
            return None
        try:
            return datetime.fromtimestamp(int(time_str))
        except:
            return None


class DouyinDataTransformer(BaseDataTransformer):
    """抖音电商数据转换器"""
    
    ORDER_STATUS_MAP = {
        1: OrderStatus.PENDING,
        2: OrderStatus.PAID,
        3: OrderStatus.PROCESSING,
        4: OrderStatus.SHIPPED,
        5: OrderStatus.DELIVERED,
        6: OrderStatus.CANCELLED
    }
    
    def transform_order(self, raw_order: Dict[str, Any]) -> OrderInfo:
        """转换抖音订单数据"""
        status_code = raw_order.get("status", 1)
        order_status = self.ORDER_STATUS_MAP.get(status_code, OrderStatus.PENDING)
        
        return OrderInfo(
            order_id=f"dy_{raw_order.get('order_id', '')}",
            platform_order_id=str(raw_order.get('order_id', '')),
            platform=PlatformType.DOUYIN,
            buyer_name=raw_order.get("post_receiver", ""),
            buyer_phone=raw_order.get("post_tel"),
            order_status=order_status.value,
            order_amount=float(raw_order.get("total_amount", 0)),
            shipping_address=raw_order.get("post_address", ""),
            items=self._extract_items(raw_order),
            created_at=self._parse_time(raw_order.get("create_time")),
            paid_at=self._parse_time(raw_order.get("pay_time")),
            shipped_at=self._parse_time(raw_order.get("ship_time")),
            shipping_tracking_number=raw_order.get("tracking_no"),
            shipping_carrier=raw_order.get("company"),
            extra_info={
                "order_status": status_code,
                "shop_id": raw_order.get("shop_id"),
                "video_id": raw_order.get("video_id")
            }
        )
    
    def transform_product(self, raw_product: Dict[str, Any]) -> ProductInfo:
        """转换抖音商品数据"""
        return ProductInfo(
            product_id=f"dy_{raw_product.get('product_id', '')}",
            platform_product_id=str(raw_product.get('product_id', '')),
            platform=PlatformType.DOUYIN,
            title=raw_product.get("name", ""),
            price=float(raw_product.get("price", 0)),
            stock=int(raw_product.get("stock_num", 0)),
            sku=str(raw_product.get("sku_id", "")),
            description=raw_product.get("description", ""),
            images=raw_product.get("img_list", []),
            category=str(raw_product.get("category_id", "")),
            is_on_sale=raw_product.get("status", 1) == 1,
            extra_info={
                "market_price": raw_product.get("market_price"),
                "comment_num": raw_product.get("comment_num")
            }
        )
    
    def _extract_items(self, raw_order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取订单商品"""
        items = raw_order.get("sku_order_list", [])
        return [
            {
                "title": item.get("item_name", ""),
                "price": float(item.get("price", 0)),
                "quantity": int(item.get("item_count", 0)),
                "sku_id": item.get("sku_id"),
                "pic_path": item.get("item_image", "")
            }
            for item in items
        ]
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间"""
        if not time_str:
            return None
        try:
            if isinstance(time_str, int):
                return datetime.fromtimestamp(time_str)
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except:
            return None


def get_data_transformer(platform_type: PlatformType) -> BaseDataTransformer:
    """获取对应平台的数据转换器"""
    transformers = {
        PlatformType.TAOBAO: TaobaoDataTransformer,
        PlatformType.JD: JDDDataTransformer,
        PlatformType.PINDUODUO: PinduoduoDataTransformer,
        PlatformType.DOUYIN: DouyinDataTransformer,
        PlatformType.XIANYU: TaobaoDataTransformer,  # 闲鱼使用淘宝相同转换器
        PlatformType.XIAOHONGSHU: BaseDataTransformer  # 小红书待定
    }
    return transformers.get(platform_type, BaseDataTransformer)()
