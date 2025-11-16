from typing import Dict, List, Any
from .virtual_disk import VirtualDisk, Inode, BlockStatus

class IntegrityChecker:
    """
    Verifica la integridad del sistema de archivos después de un fallo
    """
    
    def __init__(self, disk: VirtualDisk):
        self.disk = disk
        
    def comprehensive_integrity_check(self) -> Dict[str, Any]:
        """
        Realiza una verificación completa de integridad
        """
        print("Iniciando verificación completa de integridad...")
        
        results = {
            "total_blocks": self.disk.total_blocks,
            "free_blocks": 0,
            "used_blocks": 0,
            "corrupted_blocks": 0,
            "inodes_checked": 0,
            "inodes_integrity_ok": 0,
            "inodes_integrity_failed": 0,
            "corrupted_files": [],
            "recoverable_files": [],
            "block_status_summary": {}
        }
        
        # Verificar estado de bloques
        for status in self.disk.block_status:
            status_name = status.name
            results["block_status_summary"][status_name] = results["block_status_summary"].get(status_name, 0) + 1
            
            if status == BlockStatus.FREE:
                results["free_blocks"] += 1
            elif status == BlockStatus.USED:
                results["used_blocks"] += 1
            elif status == BlockStatus.CORRUPTED:
                results["corrupted_blocks"] += 1
        
        # Verificar integridad de inodos
        for inode_id, inode in self.disk.inodes.items():
            results["inodes_checked"] += 1
            
            # Verificar si todos los bloques del inodo están accesibles
            blocks_accessible = all(
                0 <= block_num < self.disk.total_blocks and
                self.disk.block_status[block_num] != BlockStatus.CORRUPTED
                for block_num in inode.blocks
            )
            
            if blocks_accessible:
                # Leer y verificar checksum
                file_data = self._read_inode_data(inode)
                if file_data is not None:
                    current_checksum = self.disk.calculate_checksum(file_data)
                    if current_checksum == inode.checksum:
                        results["inodes_integrity_ok"] += 1
                        results["recoverable_files"].append({
                            "inode_id": inode_id,
                            "size": inode.size,
                            "blocks_used": len(inode.blocks),
                            "status": "INTEGRITY_OK",
                            "checksum_match": True
                        })
                    else:
                        results["inodes_integrity_failed"] += 1
                        results["corrupted_files"].append({
                            "inode_id": inode_id,
                            "expected_checksum": inode.checksum[:16] + "...",
                            "actual_checksum": current_checksum[:16] + "...",
                            "status": "CHECKSUM_MISMATCH",
                            "recoverable": False
                        })
                else:
                    results["inodes_integrity_failed"] += 1
                    results["corrupted_files"].append({
                        "inode_id": inode_id,
                        "status": "UNABLE_TO_READ",
                        "recoverable": False
                    })
            else:
                results["inodes_integrity_failed"] += 1
                # Verificar cuántos bloques están corruptos
                corrupted_blocks = [b for b in inode.blocks 
                                  if self.disk.block_status[b] == BlockStatus.CORRUPTED]
                results["corrupted_files"].append({
                    "inode_id": inode_id,
                    "status": "CORRUPTED_BLOCKS",
                    "corrupted_blocks_count": len(corrupted_blocks),
                    "total_blocks": len(inode.blocks),
                    "recoverable": len(corrupted_blocks) < len(inode.blocks)  # Parcialmente recuperable
                })
        
        print(f"Verificación completada: {results['inodes_integrity_ok']}/{results['inodes_checked']} archivos intactos")
        return results
    
    def _read_inode_data(self, inode: Inode) -> bytes:
        """Intenta leer datos de un inodo"""
        try:
            data_blocks = []
            for block_num in inode.blocks:
                block_data = self.disk.read_block(block_num)
                if block_data:
                    data_blocks.append(block_data)
                else:
                    return None
            return b''.join(data_blocks)[:inode.size]
        except Exception as e:
            print(f"Error leyendo inodo {inode.id}: {e}")
            return None
    
    def compare_fs_states(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara el estado del sistema de archivos antes y después de un fallo
        """
        comparison = {
            "blocks_lost": before["used_blocks"] - after["used_blocks"],
            "new_corruptions": after["corrupted_blocks"],
            "files_recovered": after["inodes_integrity_ok"],
            "files_lost": len(after["corrupted_files"]),
            "recovery_rate": (after["inodes_integrity_ok"] / before["inodes_checked"] * 100) 
            if before["inodes_checked"] > 0 else 0,
            "data_integrity_score": (after["inodes_integrity_ok"] / after["inodes_checked"] * 100)
            if after["inodes_checked"] > 0 else 0
        }
        
        return comparison
        
    def print_detailed_report(self, integrity_results: Dict[str, Any]):
        """Imprime un reporte detallado de integridad"""
        print("\n" + "="*60)
        print("REPORTE DETALLADO DE INTEGRIDAD")
        print("="*60)
        
        print(f"\nESTADO DE BLOQUES:")
        for status, count in integrity_results["block_status_summary"].items():
            percentage = (count / integrity_results["total_blocks"]) * 100
            print(f"   • {status}: {count} bloques ({percentage:.1f}%)")
        
        print(f"\nESTADO DE ARCHIVOS:")
        print(f"   • Archivos verficados: {integrity_results['inodes_checked']}")
        print(f"   • Archivos intactos: {integrity_results['inodes_integrity_ok']}")
        print(f"   • Archivos corruptos: {integrity_results['inodes_integrity_failed']}")
        
        recovery_rate = (integrity_results['inodes_integrity_ok'] / 
                        integrity_results['inodes_checked'] * 100) if integrity_results['inodes_checked'] > 0 else 0
        print(f"   • Tasa de recuperación: {recovery_rate:.1f}%")
        
        if integrity_results["corrupted_files"]:
            print(f"\nARCHIVOS CORRUPTOS:")
            for corrupted in integrity_results["corrupted_files"][:5]:  # Mostrar primeros 5
                print(f"   • Inodo {corrupted['inode_id']}: {corrupted['status']}")
            if len(integrity_results["corrupted_files"]) > 5:
                print(f"   • ... y {len(integrity_results['corrupted_files']) - 5} más")