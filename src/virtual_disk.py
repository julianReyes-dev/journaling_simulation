import os
import struct
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class BlockStatus(Enum):
    FREE = 0
    USED = 1
    CORRUPTED = 2

@dataclass
class Inode:
    id: int
    size: int
    blocks: List[int]
    checksum: str
    created: float
    modified: float

class VirtualDisk:
    """
    Simula un disco virtual con bloques de almacenamiento
    """
    
    def __init__(self, size_mb: int = 10, block_size_kb: int = 4):
        self.block_size = block_size_kb * 1024  # 4KB blocks
        self.total_blocks = (size_mb * 1024 * 1024) // self.block_size
        self.blocks = [bytearray(self.block_size) for _ in range(self.total_blocks)]
        self.block_status = [BlockStatus.FREE] * self.total_blocks
        self.inodes: Dict[int, Inode] = {}
        self.next_inode_id = 1
        
    def write_block(self, block_num: int, data: bytes) -> bool:
        """Escribe datos en un bloque específico"""
        if block_num < 0 or block_num >= self.total_blocks:
            return False
            
        if len(data) > self.block_size:
            data = data[:self.block_size]
            
        self.blocks[block_num][:] = data.ljust(self.block_size, b'\x00')
        self.block_status[block_num] = BlockStatus.USED
        return True
        
    def read_block(self, block_num: int) -> Optional[bytes]:
        """Lee datos de un bloque específico"""
        if block_num < 0 or block_num >= self.total_blocks:
            return None
        return bytes(self.blocks[block_num])
        
    def mark_corrupted(self, block_num: int):
        """Marca un bloque como corrupto (simulación de fallo)"""
        if 0 <= block_num < self.total_blocks:
            self.block_status[block_num] = BlockStatus.CORRUPTED
            
    def get_free_blocks(self, count: int) -> List[int]:
        """Encuentra bloques libres consecutivos"""
        free_blocks = []
        for i, status in enumerate(self.block_status):
            if status == BlockStatus.FREE:
                free_blocks.append(i)
                if len(free_blocks) == count:
                    break
        return free_blocks if len(free_blocks) == count else []
        
    def calculate_checksum(self, data: bytes) -> str:
        """Calcula checksum para verificar integridad"""
        return hashlib.sha256(data).hexdigest()
        
    def get_disk_stats(self) -> Dict[str, any]:
        """Retorna estadísticas del disco"""
        return {
            "total_blocks": self.total_blocks,
            "free_blocks": sum(1 for s in self.block_status if s == BlockStatus.FREE),
            "used_blocks": sum(1 for s in self.block_status if s == BlockStatus.USED),
            "corrupted_blocks": sum(1 for s in self.block_status if s == BlockStatus.CORRUPTED),
            "total_inodes": len(self.inodes)
        }