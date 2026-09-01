/*
 Navicat Premium Dump SQL

 Source Server         : Smart_MGED
 Source Server Type    : MySQL
 Source Server Version : 90600 (9.6.0)
 Source Host           : localhost:3306
 Source Schema         : smart_small

 Target Server Type    : MySQL
 Target Server Version : 90600 (9.6.0)
 File Encoding         : 65001

 Date: 27/07/2026 21:27:50
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for property_table
-- ----------------------------
DROP TABLE IF EXISTS `property_table`;
CREATE TABLE `property_table`  (
  `property_id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `property_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `property_description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`property_id`) USING BTREE,
  UNIQUE INDEX `uk_property_name`(`property_name` ASC) USING BTREE,
  INDEX `idx_property_table_property_name`(`property_name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 247 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of property_table
-- ----------------------------
INSERT INTO `property_table` VALUES (1, 'material_name', '材料名称或材料牌号，用于唯一标识材料类型，例如Q235、304不锈钢、Ti6Al4V钛合金等，是材料数据库中的基础索引字段');
INSERT INTO `property_table` VALUES (2, 'standard', '材料执行标准编号或测试依据，例如GB、ASTM、ISO、DIN或JIS等国际或国家标准，用于描述材料生产与检测所遵循的技术规范');
INSERT INTO `property_table` VALUES (3, 'classification', '材料分类信息，例如碳钢、不锈钢、工具钢、铝合金、钛合金、高温合金或复合材料等，用于材料数据库分类管理');
INSERT INTO `property_table` VALUES (4, 'corresponding_grade', '对应国际或国内等效材料牌号，用于不同标准体系之间材料牌号的对照关系');
INSERT INTO `property_table` VALUES (5, 'batch_id', '材料生产炉号或批次编号，用于材料质量追溯及实验数据来源记录');
INSERT INTO `property_table` VALUES (6, 'chemical_formula', '材料化学组成或化学式表达，用于描述材料的元素组成情况');
INSERT INTO `property_table` VALUES (7, 'density', '材料密度，表示单位体积材料所具有的质量，是材料重要的物理性能指标');
INSERT INTO `property_table` VALUES (8, 'melting_point', '材料熔点温度，表示材料从固态转变为液态时的温度');
INSERT INTO `property_table` VALUES (9, 'thermal_conductivity', '材料导热系数，用于描述材料传递热量的能力');
INSERT INTO `property_table` VALUES (10, 'electrical_resistivity', '材料电阻率，用于描述材料对电流传导的阻碍能力');
INSERT INTO `property_table` VALUES (11, 'specific_heat', '材料比热容，表示单位质量材料温度升高单位温度所需要吸收的热量');
INSERT INTO `property_table` VALUES (12, 'thermal_expansion', '材料线膨胀系数，表示材料在温度变化时尺寸变化的程度');
INSERT INTO `property_table` VALUES (13, 'grain_size', '材料晶粒尺寸或晶粒等级，用于描述材料显微组织结构特征');
INSERT INTO `property_table` VALUES (14, 'phase_structure', '材料相结构类型，例如奥氏体、铁素体、马氏体或多相组织结构');
INSERT INTO `property_table` VALUES (15, 'microstructure', '材料显微组织描述，例如珠光体组织、贝氏体组织或马氏体组织');
INSERT INTO `property_table` VALUES (16, 'supplier', '材料生产厂家或供应商名称，用于记录材料来源');
INSERT INTO `property_table` VALUES (17, 'production_process', '材料生产工艺，例如铸造、锻造、轧制、粉末冶金或增材制造');
INSERT INTO `property_table` VALUES (18, 'surface_condition', '材料表面状态，例如抛光、喷砂、氧化或镀层处理');
INSERT INTO `property_table` VALUES (19, 'coating', '材料表面涂层或镀层类型，例如镀锌层、陶瓷涂层或防腐涂层');
INSERT INTO `property_table` VALUES (20, 'remarks', '材料附加备注信息，用于记录特殊说明或实验备注');
INSERT INTO `property_table` VALUES (21, 'yield_strength', '材料屈服强度，单位MPa，表示材料开始产生明显塑性变形时所对应的应力值');
INSERT INTO `property_table` VALUES (22, 'tensile_strength', '材料抗拉强度，单位MPa，表示材料在拉伸试验中能够承受的最大应力');
INSERT INTO `property_table` VALUES (23, 'compressive_strength', '材料抗压强度，单位MPa，表示材料在压缩载荷作用下能够承受的最大应力');
INSERT INTO `property_table` VALUES (24, 'shear_strength', '材料抗剪强度，单位MPa，用于描述材料抵抗剪切破坏的能力');
INSERT INTO `property_table` VALUES (25, 'elastic_modulus', '材料弹性模量，单位GPa，用于描述材料在弹性变形阶段应力与应变之间的比例关系');
INSERT INTO `property_table` VALUES (26, 'poisson_ratio', '材料泊松比，表示材料在受力变形时横向应变与纵向应变之间的比例关系');
INSERT INTO `property_table` VALUES (27, 'hardness_hv', '材料维氏硬度HV，通过金刚石压头压入试样表面测量材料硬度');
INSERT INTO `property_table` VALUES (28, 'hardness_hrc', '材料洛氏硬度HRC，用于表示材料抵抗塑性变形或压入的能力');
INSERT INTO `property_table` VALUES (29, 'impact_energy', '材料冲击吸收能量，单位J，用于描述材料在冲击试验中吸收能量的能力');
INSERT INTO `property_table` VALUES (30, 'impact_toughness', '材料冲击韧性，单位J/cm²，用于评价材料抵抗冲击断裂的能力');
INSERT INTO `property_table` VALUES (31, 'elongation', '材料断后伸长率，单位%，表示材料塑性变形能力的重要指标');
INSERT INTO `property_table` VALUES (32, 'reduction_area', '材料断面收缩率，单位%，表示材料在拉伸断裂后截面积减少比例');
INSERT INTO `property_table` VALUES (33, 'fatigue_strength', '材料疲劳强度，用于描述材料在循环载荷作用下抵抗疲劳破坏的能力');
INSERT INTO `property_table` VALUES (34, 'creep_strength', '材料蠕变强度，用于描述材料在高温长期载荷作用下抵抗塑性变形的能力');
INSERT INTO `property_table` VALUES (35, 'H', '氢元素质量分数，单位wt%，氢元素在金属材料中可能引起氢脆现象');
INSERT INTO `property_table` VALUES (36, 'He', '氦元素质量分数，单位wt%，氦通常为惰性气体，在材料中含量极低');
INSERT INTO `property_table` VALUES (37, 'Li', '锂元素质量分数，单位wt%，锂在轻合金材料中常作为强化元素');
INSERT INTO `property_table` VALUES (38, 'Be', '铍元素质量分数，单位wt%，铍元素常用于高强度轻质合金材料');
INSERT INTO `property_table` VALUES (39, 'B', '硼元素质量分数，单位wt%，硼能够显著提高钢材的淬透性');
INSERT INTO `property_table` VALUES (40, 'C', '碳元素质量分数，单位wt%，碳是钢铁材料中最重要的强化元素之一');
INSERT INTO `property_table` VALUES (41, 'N', '氮元素质量分数，单位wt%，氮能够提高钢材强度并形成氮化物强化相');
INSERT INTO `property_table` VALUES (42, 'O', '氧元素质量分数，单位wt%，氧通常作为杂质元素存在于金属材料中');
INSERT INTO `property_table` VALUES (43, 'F', '氟元素质量分数，单位wt%，氟元素通常存在于某些特殊化学材料中');
INSERT INTO `property_table` VALUES (44, 'Ne', '氖元素质量分数，单位wt%，惰性气体元素，在材料中含量极低');
INSERT INTO `property_table` VALUES (45, 'Na', '钠元素质量分数，单位wt%，钠在某些合金体系中作为微量元素存在');
INSERT INTO `property_table` VALUES (46, 'Mg', '镁元素质量分数，单位wt%，镁是轻金属合金中的重要元素');
INSERT INTO `property_table` VALUES (47, 'Al', '铝元素质量分数，单位wt%，铝可用于钢材脱氧并提高耐腐蚀性能');
INSERT INTO `property_table` VALUES (48, 'Si', '硅元素质量分数，单位wt%，硅可提高材料强度并改善铸造性能');
INSERT INTO `property_table` VALUES (49, 'P', '磷元素质量分数，单位wt%，磷通常为杂质元素，会降低钢材韧性');
INSERT INTO `property_table` VALUES (50, 'S', '硫元素质量分数，单位wt%，硫可能导致材料产生热脆现象');
INSERT INTO `property_table` VALUES (51, 'Cl', '氯元素质量分数，单位wt%，氯在某些腐蚀环境中对材料性能有影响');
INSERT INTO `property_table` VALUES (52, 'Ar', '氩元素质量分数，单位wt%，氩通常作为保护气体存在');
INSERT INTO `property_table` VALUES (53, 'K', '钾元素质量分数，单位wt%，钾在金属材料中一般为微量杂质元素');
INSERT INTO `property_table` VALUES (54, 'Ca', '钙元素质量分数，单位wt%，钙可用于钢液夹杂物变性处理');
INSERT INTO `property_table` VALUES (55, 'Sc', '钪元素质量分数，单位wt%，钪可用于强化铝合金');
INSERT INTO `property_table` VALUES (56, 'Ti', '钛元素质量分数，单位wt%，钛可提高材料强度并形成稳定碳化物');
INSERT INTO `property_table` VALUES (57, 'V', '钒元素质量分数，单位wt%，钒可通过细化晶粒提高材料强度');
INSERT INTO `property_table` VALUES (58, 'Cr', '铬元素质量分数，单位wt%，铬可提高材料耐腐蚀性和耐磨性能');
INSERT INTO `property_table` VALUES (59, 'Mn', '锰元素质量分数，单位wt%，锰可提高钢材强度并改善淬透性');
INSERT INTO `property_table` VALUES (60, 'Fe', '铁元素质量分数，单位wt%，铁是钢铁材料的主要基体元素');
INSERT INTO `property_table` VALUES (61, 'Co', '钴元素质量分数，单位wt%，钴可提高高温合金的耐热性能');
INSERT INTO `property_table` VALUES (62, 'Ni', '镍元素质量分数，单位wt%，镍可提高材料韧性和耐腐蚀性能');
INSERT INTO `property_table` VALUES (63, 'Cu', '铜元素质量分数，单位wt%，铜可提高材料耐腐蚀能力');
INSERT INTO `property_table` VALUES (64, 'Zn', '锌元素质量分数，单位wt%，锌通常用于防腐镀层材料');
INSERT INTO `property_table` VALUES (65, 'Ga', '镓元素质量分数，单位wt%，镓在电子材料中具有重要应用');
INSERT INTO `property_table` VALUES (66, 'Ge', '锗元素质量分数，单位wt%，锗是重要的半导体材料元素');
INSERT INTO `property_table` VALUES (67, 'As', '砷元素质量分数，单位wt%，砷在材料中通常为微量杂质元素');
INSERT INTO `property_table` VALUES (68, 'Se', '硒元素质量分数，单位wt%，硒可改善某些钢材的切削性能');
INSERT INTO `property_table` VALUES (69, 'Br', '溴元素质量分数，单位wt%，溴在材料中通常作为痕量元素存在');
INSERT INTO `property_table` VALUES (70, 'Kr', '氪元素质量分数，单位wt%，惰性气体元素');
INSERT INTO `property_table` VALUES (71, 'Rb', '铷元素质量分数，单位wt%，碱金属元素');
INSERT INTO `property_table` VALUES (72, 'Sr', '锶元素质量分数，单位wt%，锶在铝合金中可用于变质处理');
INSERT INTO `property_table` VALUES (73, 'Y', '钇元素质量分数，单位wt%，钇可用于改善合金高温性能');
INSERT INTO `property_table` VALUES (74, 'Zr', '锆元素质量分数，单位wt%，锆可细化晶粒并提高耐腐蚀性能');
INSERT INTO `property_table` VALUES (75, 'Nb', '铌元素质量分数，单位wt%，铌可通过形成碳化物强化材料');
INSERT INTO `property_table` VALUES (76, 'Mo', '钼元素质量分数，单位wt%，钼可提高材料高温强度和抗蠕变性能');
INSERT INTO `property_table` VALUES (77, 'Tc', '锝元素质量分数，单位wt%，锝属于放射性过渡金属元素，在材料工程应用中较少出现');
INSERT INTO `property_table` VALUES (78, 'Ru', '钌元素质量分数，单位wt%，钌属于铂族金属元素，可用于提高材料耐腐蚀性能');
INSERT INTO `property_table` VALUES (79, 'Rh', '铑元素质量分数，单位wt%，铑属于贵金属元素，在催化材料及高温合金中具有应用');
INSERT INTO `property_table` VALUES (80, 'Pd', '钯元素质量分数，单位wt%，钯属于铂族金属元素，在催化剂和电子材料中应用广泛');
INSERT INTO `property_table` VALUES (81, 'Ag', '银元素质量分数，单位wt%，银具有优良导电和导热性能，常用于电子材料');
INSERT INTO `property_table` VALUES (82, 'Cd', '镉元素质量分数，单位wt%，镉通常存在于某些合金或镀层材料中');
INSERT INTO `property_table` VALUES (83, 'In', '铟元素质量分数，单位wt%，铟是重要的半导体和电子功能材料元素');
INSERT INTO `property_table` VALUES (84, 'Sn', '锡元素质量分数，单位wt%，锡常用于焊料材料及防腐合金');
INSERT INTO `property_table` VALUES (85, 'Sb', '锑元素质量分数，单位wt%，锑可用于提高合金硬度和耐磨性能');
INSERT INTO `property_table` VALUES (86, 'Te', '碲元素质量分数，单位wt%，碲在某些钢材中可改善切削加工性能');
INSERT INTO `property_table` VALUES (87, 'I', '碘元素质量分数，单位wt%，碘属于卤素元素，在材料中一般为微量存在');
INSERT INTO `property_table` VALUES (88, 'Xe', '氙元素质量分数，单位wt%，氙属于惰性气体元素，在材料中通常极微量存在');
INSERT INTO `property_table` VALUES (89, 'Cs', '铯元素质量分数，单位wt%，铯属于碱金属元素，在某些特殊材料体系中存在');
INSERT INTO `property_table` VALUES (90, 'Ba', '钡元素质量分数，单位wt%，钡可用于某些合金材料或功能陶瓷材料');
INSERT INTO `property_table` VALUES (91, 'La', '镧元素质量分数，单位wt%，镧属于稀土元素，可用于改善合金组织性能');
INSERT INTO `property_table` VALUES (92, 'Ce', '铈元素质量分数，单位wt%，铈属于稀土元素，可用于钢铁脱氧和净化');
INSERT INTO `property_table` VALUES (93, 'Pr', '镨元素质量分数，单位wt%，镨属于稀土元素，可用于改善磁性材料性能');
INSERT INTO `property_table` VALUES (94, 'Nd', '钕元素质量分数，单位wt%，钕是高性能永磁材料的重要组成元素');
INSERT INTO `property_table` VALUES (95, 'Pm', '钷元素质量分数，单位wt%，钷属于稀土放射性元素，在材料中极少使用');
INSERT INTO `property_table` VALUES (96, 'Sm', '钐元素质量分数，单位wt%，钐属于稀土元素，在磁性材料和高温材料中具有应用');
INSERT INTO `property_table` VALUES (97, 'Eu', '铕元素质量分数，单位wt%，铕属于稀土元素，常用于发光材料');
INSERT INTO `property_table` VALUES (98, 'Gd', '钆元素质量分数，单位wt%，钆属于稀土元素，可用于核材料和磁性材料');
INSERT INTO `property_table` VALUES (99, 'Tb', '铽元素质量分数，单位wt%，铽属于稀土元素，在磁致伸缩材料中应用较多');
INSERT INTO `property_table` VALUES (100, 'Dy', '镝元素质量分数，单位wt%，镝属于稀土元素，可提高永磁材料耐热性能');
INSERT INTO `property_table` VALUES (101, 'Ho', '钬元素质量分数，单位wt%，钬属于稀土元素，在特殊功能材料中应用');
INSERT INTO `property_table` VALUES (102, 'Er', '铒元素质量分数，单位wt%，铒属于稀土元素，在光纤通信材料中应用较多');
INSERT INTO `property_table` VALUES (103, 'Tm', '铥元素质量分数，单位wt%，铥属于稀土元素，在某些激光材料中使用');
INSERT INTO `property_table` VALUES (104, 'Yb', '镱元素质量分数，单位wt%，镱属于稀土元素，在功能合金材料中应用');
INSERT INTO `property_table` VALUES (105, 'Lu', '镥元素质量分数，单位wt%，镥属于稀土元素，在高密度合金材料中具有研究价值');
INSERT INTO `property_table` VALUES (106, 'Hf', '铪元素质量分数，单位wt%，铪属于过渡金属元素，可提高合金耐高温性能');
INSERT INTO `property_table` VALUES (107, 'Ta', '钽元素质量分数，单位wt%，钽具有优良耐腐蚀性能，在高温合金和电子材料中应用');
INSERT INTO `property_table` VALUES (108, 'W', '钨元素质量分数，单位wt%，钨可显著提高材料高温强度和硬度');
INSERT INTO `property_table` VALUES (109, 'Re', '铼元素质量分数，单位wt%，铼可显著提高高温合金的耐高温性能');
INSERT INTO `property_table` VALUES (110, 'Os', '锇元素质量分数，单位wt%，锇属于铂族金属元素，在材料工程中应用较少');
INSERT INTO `property_table` VALUES (111, 'Ir', '铱元素质量分数，单位wt%，铱属于高熔点贵金属元素，在高温环境中具有稳定性能');
INSERT INTO `property_table` VALUES (112, 'Pt', '铂元素质量分数，单位wt%，铂属于贵金属元素，在催化材料及电子材料中应用广泛');
INSERT INTO `property_table` VALUES (113, 'Au', '金元素质量分数，单位wt%，金具有优良导电和抗腐蚀性能，常用于电子器件材料');
INSERT INTO `property_table` VALUES (114, 'Hg', '汞元素质量分数，单位wt%，汞在金属材料中通常作为杂质元素存在');
INSERT INTO `property_table` VALUES (115, 'Tl', '铊元素质量分数，单位wt%，铊在某些特殊电子材料中具有应用');
INSERT INTO `property_table` VALUES (116, 'Pb', '铅元素质量分数，单位wt%，铅在某些合金材料中用于改善加工性能');
INSERT INTO `property_table` VALUES (117, 'Bi', '铋元素质量分数，单位wt%，铋可用于改善材料切削性能');
INSERT INTO `property_table` VALUES (118, 'grain_id', '晶粒编号，用于标识显微组织分析结果中单个晶粒或特征单元的唯一编号，常用于EBSD、三维重构或图像分割后的对象索引');
INSERT INTO `property_table` VALUES (119, 'grain_face_count', '晶粒面数，表示三维晶粒或显微组织特征单元所具有的界面/多面体面数量，用于表征晶粒拓扑结构复杂程度');
INSERT INTO `property_table` VALUES (120, 'grain_position', '晶粒位置，表示晶粒或显微组织特征单元在样品中的相对空间位置，例如外层、中间层、内层、表层或芯部');
INSERT INTO `property_table` VALUES (121, 'grain_volume', '晶粒体积，表示单个晶粒或显微组织特征单元所占据的体积大小，常用于三维组织表征与统计分析');
INSERT INTO `property_table` VALUES (122, 'grain_radius', '晶粒半径，表示单个晶粒或显微组织特征单元的特征半径，可用于反映晶粒尺度大小');
INSERT INTO `property_table` VALUES (123, 'grain_surface_area', '晶粒表面积，表示单个晶粒或显微组织特征单元的表面面积或界面面积，用于表征其几何特征与界面复杂程度');
INSERT INTO `property_table` VALUES (124, 'external_database_id', '外部材料数据库记录编号，用于标识材料在第三方数据库中的唯一记录ID，例如MatHub-3d、Materials Project、OQMD等数据库中的条目编号');
INSERT INTO `property_table` VALUES (125, 'carrier_concentration_p_type', 'p型载流子浓度，用于描述材料在p-type输运条件下的载流子浓度，单位及表达形式依数据源定义');
INSERT INTO `property_table` VALUES (126, 'seebeck_coefficient_p_type', 'p型泽贝克系数，用于描述材料在p-type输运条件下的热电势响应能力，常用单位为μV/K');
INSERT INTO `property_table` VALUES (127, 'electrical_conductivity_p_type', 'p型电导率，用于描述材料在p-type输运条件下的导电能力，单位依数据源定义，常见为S/m');
INSERT INTO `property_table` VALUES (128, 'electronic_thermal_conductivity_p_type', 'p型电子热导率，用于描述材料在p-type输运条件下由电子贡献的热传导能力，常见单位为W/(m·K)');
INSERT INTO `property_table` VALUES (129, 'carrier_concentration_n_type', 'n型载流子浓度，用于描述材料在n-type输运条件下的载流子浓度，单位及表达形式依数据源定义');
INSERT INTO `property_table` VALUES (130, 'seebeck_coefficient_n_type', 'n型泽贝克系数，用于描述材料在n-type输运条件下的热电势响应能力，常用单位为μV/K');
INSERT INTO `property_table` VALUES (131, 'electrical_conductivity_n_type', 'n型电导率，用于描述材料在n-type输运条件下的导电能力，单位依数据源定义，常见为S/m');
INSERT INTO `property_table` VALUES (132, 'electronic_thermal_conductivity_n_type', 'n型电子热导率，用于描述材料在n-type输运条件下由电子贡献的热传导能力，常见单位为W/(m·K)');
INSERT INTO `property_table` VALUES (133, 'data_description', '材料性能数据说明字段，用于描述该条数据对应的测量数据、模拟数据、插值数据、拟合数据或经后处理得到的数据内容与来源');
INSERT INTO `property_table` VALUES (134, 'temperature', '测试温度或计算温度，通常单位为K或℃，用于记录材料性能数据对应的温度条件');
INSERT INTO `property_table` VALUES (135, 'data_value', '材料性能数据值，用于记录某一温度、条件或测试/模拟场景下得到的具体数值结果，单位依具体属性而定');
INSERT INTO `property_table` VALUES (136, 'collection_time', '数据采集时间，用于记录材料测试、监测或环境暴露数据的实际采集时间戳');
INSERT INTO `property_table` VALUES (137, 'location_name', '采集地点或试验地点名称，用于记录材料测试、服役监测或环境暴露所在区域');
INSERT INTO `property_table` VALUES (138, 'longitude', '地理经度，单位为度，用于记录材料测试或环境暴露位置的经度坐标');
INSERT INTO `property_table` VALUES (139, 'latitude', '地理纬度，单位为度，用于记录材料测试或环境暴露位置的纬度坐标');
INSERT INTO `property_table` VALUES (140, 'test_method', '试验方法或测试方法，用于描述材料性能数据所采用的实验、表征或分析方法');
INSERT INTO `property_table` VALUES (141, 'humidity', '环境湿度，通常为相对湿度，单位为%，用于记录材料测试或服役环境中的湿度条件');
INSERT INTO `property_table` VALUES (142, 'chloride_deposition', '氯离子沉积量或环境氯离子负荷，用于描述材料暴露环境中氯盐沉积水平，单位依数据来源定义，例如mg/m2');
INSERT INTO `property_table` VALUES (143, 'pH', '环境介质或液膜的pH值，用于描述材料测试或腐蚀环境中的酸碱度条件');
INSERT INTO `property_table` VALUES (144, 'electrolyte_film_resistance', '液膜电阻或电解质液膜电阻，单位通常为Ω·cm2，用于表征材料表面电解质液膜对电流传输的阻抗特性');
INSERT INTO `property_table` VALUES (145, 'polarization_resistance', '极化电阻，单位通常为Ω·cm2，用于评价材料在电化学腐蚀过程中的极化阻抗特征');
INSERT INTO `property_table` VALUES (146, 'open_circuit_potential', '开路电位，单位通常为mV，用于描述材料在无外加电流条件下的稳定电极电位');
INSERT INTO `property_table` VALUES (147, 'calculation_model', '计算模型或计算公式，用于描述材料性能指标由原始测量参数推导得到时所采用的模型、公式或算法');
INSERT INTO `property_table` VALUES (148, 'corrosion_rate', '腐蚀速率，用于描述材料在特定环境中的腐蚀发展速度，单位依数据来源定义，例如μm/a');
INSERT INTO `property_table` VALUES (149, 'accumulated_corrosion_depth', '累计腐蚀深度或已腐蚀量，用于描述材料在一定暴露时间后累计产生的腐蚀损失厚度，常见单位为μm');
INSERT INTO `property_table` VALUES (150, 'heat_treatment_type', '热处理工艺类型或热处理步骤名称，例如固溶、时效、退火、淬火、回火等，用于描述材料所经历的热处理阶段');
INSERT INTO `property_table` VALUES (151, 'heat_treatment_temperature', '热处理温度，通常单位为℃，用于记录材料在固溶、时效、退火等热处理过程中的设定温度');
INSERT INTO `property_table` VALUES (152, 'heat_treatment_time', '热处理时间或保温时间，用于记录材料在特定热处理步骤中的持续处理时长，单位依数据来源定义，例如min或h');
INSERT INTO `property_table` VALUES (153, 'cooling_method', '冷却方式，用于描述材料在热处理步骤完成后的冷却条件，例如空冷、水冷、油冷、炉冷等');
INSERT INTO `property_table` VALUES (154, 'gamma_prime_volume_fraction', 'γ\'相体积分数，单位通常为%，用于描述高温合金等材料中γ\'强化相在显微组织中的体积分数，是评价组织稳定性和高温性能的重要参数');
INSERT INTO `property_table` VALUES (155, 'process_description', '工艺说明或工艺参数描述，用于记录材料加工、处理或制备过程中的详细参数与条件，例如功率、能量密度、持续时间、频率、束斑尺寸等');
INSERT INTO `property_table` VALUES (156, 'material_condition', '材料状态或试样状态，用于描述材料在测试或表征时所处的组织、热处理、加工或服役状态，例如退火态、冷轧态、固溶态、时效态等');
INSERT INTO `property_table` VALUES (157, 'relative_position_x', '相对位置X坐标，用于记录材料截面、表面或组织区域内测试点的相对横向位置');
INSERT INTO `property_table` VALUES (158, 'relative_position_y', '相对位置Y坐标，用于记录材料截面、表面或组织区域内测试点的相对纵向位置');
INSERT INTO `property_table` VALUES (159, 'test_condition', '测试条件，用于记录材料性能测试、表征或模拟时的综合条件描述，例如温度、加载方式、扫描模式、频率范围或应力/应变控制方式');
INSERT INTO `property_table` VALUES (160, 'shear_stress', '剪切应力，用于记录流变测试、剪切加载或相关实验过程中施加或对应的剪切应力数值，单位依数据来源定义');
INSERT INTO `property_table` VALUES (161, 'rheological_modulus', '流变模量，用于记录材料在流变测试条件下测得的模量相关结果，适用于未进一步区分储能模量、损耗模量或复数模量的场景，单位依数据来源定义');
INSERT INTO `property_table` VALUES (162, 'shear_rate', '剪切速率，用于记录流变测试、稳态流动测试或剪切条件下的剪切速率数值，单位依数据来源定义，常见为s^-1');
INSERT INTO `property_table` VALUES (163, 'viscosity', '黏度或动力黏度，用于描述流体、浆料或高分子体系在流动过程中对剪切变形的阻力，单位依数据来源定义，常见为Pa·s或mPa·s');
INSERT INTO `property_table` VALUES (164, 'strain', '应变，用于记录材料在加载、变形、腐蚀力学或其他测试过程中产生的变形程度，可用于应力-应变曲线、慢应变速率拉伸或原位测试数据记录');
INSERT INTO `property_table` VALUES (165, 'stress', '应力，用于记录材料在拉伸、压缩、腐蚀力学或其他加载测试过程中的受力水平，可用于应力-应变曲线或过程数据点记录，单位依数据来源定义，常见为MPa');
INSERT INTO `property_table` VALUES (166, 'process_code', '工艺代号或工艺编号，用于标识特定加工工艺、热处理制度或实验工艺路线的内部编号');
INSERT INTO `property_table` VALUES (167, 'testing_institution', '试验单位或检测机构名称，用于记录材料性能测试、实验或表征工作的执行单位');
INSERT INTO `property_table` VALUES (168, 'sample_size', '试样尺寸，用于记录材料试样的几何尺寸规格，例如长度、宽度、厚度或标准试样尺寸');
INSERT INTO `property_table` VALUES (169, 'specimen_type', '试样类型，用于描述试样的类别、缺口形式或标准类型，例如U型、V型、板状、棒状等');
INSERT INTO `property_table` VALUES (170, 'sampling_direction', '取样方向，用于记录试样相对于材料加工方向、轧制方向、挤压方向或锻造方向的取样方位，例如纵向、横向等');
INSERT INTO `property_table` VALUES (171, 'tempering_process', '回火工艺制度，用于记录材料回火处理的温度、时间及冷却方式等具体热处理参数');
INSERT INTO `property_table` VALUES (172, 'quenching_process', '淬火工艺制度，用于记录材料淬火处理的温度、保温时间及冷却方式等具体热处理参数');
INSERT INTO `property_table` VALUES (173, 'pre_treatment_process', '预处理工艺制度，用于记录材料在正式热处理或服役前进行的预处理步骤及其温度、时间、冷却方式等参数');
INSERT INTO `property_table` VALUES (174, 'quenching_and_tempering_process', '调质处理工艺制度，用于记录材料经淬火和回火组合处理所采用的完整热处理参数');
INSERT INTO `property_table` VALUES (175, 'stress_relief_process', '除应力处理工艺制度，用于记录材料为消除残余应力而进行的热处理条件及其温度、时间和冷却方式');
INSERT INTO `property_table` VALUES (176, 'specification', '材料或样品的型号规格信息，用于记录产品规格、尺寸等级、强度等级或型号标识等内容');
INSERT INTO `property_table` VALUES (177, 'inclusion_rating', '夹杂物评级或夹杂物级别，用于描述材料中氧化物、硫化物等非金属夹杂物的等级、数量或严重程度');
INSERT INTO `property_table` VALUES (178, 'normalizing_process', '正火工艺制度，用于记录材料正火处理的温度、保温时间及冷却方式等具体热处理参数');
INSERT INTO `property_table` VALUES (179, 'maximum_grain_size', '最大晶粒度，用于描述材料显微组织中观测到的最大晶粒等级或最大晶粒尺寸特征');
INSERT INTO `property_table` VALUES (180, 'notch_shape', '缺口形状或缺口状态，用于描述冲击试样、断裂试样或力学试样的缺口形式，例如U型、V型、光滑等');
INSERT INTO `property_table` VALUES (181, 'sample_count', '样品数量或试样数量，用于记录同一测试条件下参与测试的样品个数');
INSERT INTO `property_table` VALUES (182, 'heat_treatment_process', '热处理工艺或热处理状态描述，用于记录未进一步细分为淬火、回火、正火、时效等具体类别时的热处理制度、热处理条件或热处理状态说明');
INSERT INTO `property_table` VALUES (183, 'application', '材料或产品用途，用于描述材料对应的使用场景、服役对象或应用方向，例如热作模具、轴承、压力容器等');
INSERT INTO `property_table` VALUES (184, 'dimension_1', '材料、样品或产品的第一尺寸参数，用于记录规格尺寸中的一个主要维度，具体含义依数据来源定义');
INSERT INTO `property_table` VALUES (185, 'dimension_2', '材料、样品或产品的第二尺寸参数，用于记录规格尺寸中的另一个主要维度，具体含义依数据来源定义');
INSERT INTO `property_table` VALUES (186, 'macro_inspection', '低倍检验或宏观组织检验结果，用于记录材料在低倍组织检验、宏观缺陷检查中的观察结果与评级结论');
INSERT INTO `property_table` VALUES (187, 'heat_treatment_state_1', '第一热处理状态，用于记录材料在第一阶段或第一类热处理后的状态描述，例如退火态、正火态、固溶态等');
INSERT INTO `property_table` VALUES (188, 'heat_treatment_state_2', '第二热处理状态，用于记录材料在第二阶段或第二类热处理后的状态描述，例如淬火态、回火态、淬火+回火态等');
INSERT INTO `property_table` VALUES (189, 'hardness', '通用硬度值，用于记录未明确标注为HV、HRC、HB等具体标尺的硬度结果');
INSERT INTO `property_table` VALUES (190, 'upper_yield_strength', '材料上屈服强度，单位MPa，表示材料开始屈服时在首次出现明显塑性变形前达到的较高应力值');
INSERT INTO `property_table` VALUES (191, 'lower_yield_strength', '材料下屈服强度，单位MPa，表示材料进入连续屈服阶段后相对稳定的较低应力值');
INSERT INTO `property_table` VALUES (192, 'test_date', '试验日期，用于记录材料性能测试、表征或实验实施的具体日期');
INSERT INTO `property_table` VALUES (193, 'thermal_diffusivity', '材料热扩散率，用于描述材料内部温度扰动传播快慢的能力，常见单位为m2/s');
INSERT INTO `property_table` VALUES (194, 'data_source_type', '数据来源类型，标识数据是实验测量数据、第一性原理模拟数据、分子动力学计算数据、文献提取数据或后处理插值数据');
INSERT INTO `property_table` VALUES (195, 'exposure_duration', '暴露时间/试验持续时间，材料在腐蚀环境、高温或特定测试条件下的持续暴露或试验时长，单位依场景而定（h/day/year）');
INSERT INTO `property_table` VALUES (196, 'image_file', '图像文件名或图像资源标识，用于记录材料显微组织图、化学结构式图、EBSD图等图像型字段所引用的图片文件路径或哈希名');
INSERT INTO `property_table` VALUES (197, 'symbol', '测试符号或标尺符号，用于记录硬度、试验方法或测量结果所采用的符号标识，例如HV、HRC、HRBW等');
INSERT INTO `property_table` VALUES (198, 'test_standard', '试验标准编号，用于记录具体性能测试、硬度试验或表征方法所依据的标准，例如ISO、ASTM、GB等');
INSERT INTO `property_table` VALUES (199, 'measurement_index1', '测次序号，用于记录同一属性在同一样品或同一测试条件下的第1次测量结果');
INSERT INTO `property_table` VALUES (200, 'measurement_index2', '测次序号，用于记录同一属性在同一样品或同一测试条件下的第2次测量结果');
INSERT INTO `property_table` VALUES (201, 'measurement_index3', '测次序号，用于记录同一属性在同一样品或同一测试条件下的第3次测量结果');
INSERT INTO `property_table` VALUES (202, 'measurement_index4', '测次序号，用于记录同一属性在同一样品或同一测试条件下的第4次测量结果');
INSERT INTO `property_table` VALUES (203, 'measurement_index5', '测次序号，用于记录同一属性在同一样品或同一测试条件下的第5次测量结果');
INSERT INTO `property_table` VALUES (204, 'sample_name', '试样名称，用于标识具体测试样件、焊接接头样件或实验样品名称');
INSERT INTO `property_table` VALUES (205, 'cold_work_degree', '冷变形程度，用于描述材料或试样经历冷加工后的变形程度，通常以百分比表示');
INSERT INTO `property_table` VALUES (206, 'product_form', '产品形态或试样形态，用于描述材料的产品形式或测试对象形态，例如板材、棒材、焊接接头等');
INSERT INTO `property_table` VALUES (207, 'heat_treatment_method', '热处理方法或热处理方法代码，用于记录试样所采用的热处理方法、状态代号或方法标识');
INSERT INTO `property_table` VALUES (208, 'stress_intensity_factor', '应力强度因子K，用于断裂力学中表征裂纹尖端应力场强度，常见单位为MPa·m^0.5');
INSERT INTO `property_table` VALUES (209, 'loading_condition', '加载条件，用于记录疲劳、断裂或腐蚀力学试验中的载荷比、频率、保持时间等加载参数');
INSERT INTO `property_table` VALUES (210, 'boron_concentration', '环境介质中硼浓度，用于记录水化学环境或腐蚀介质中的硼含量，单位依数据来源定义');
INSERT INTO `property_table` VALUES (211, 'lithium_concentration', '环境介质中锂浓度，用于记录水化学环境或腐蚀介质中的锂含量，单位依数据来源定义');
INSERT INTO `property_table` VALUES (212, 'chloride_concentration', '环境介质中氯离子浓度，用于记录水化学环境或腐蚀介质中的氯离子含量，单位依数据来源定义');
INSERT INTO `property_table` VALUES (213, 'potassium_concentration', '环境介质中钾浓度，用于记录水化学环境或腐蚀介质中的钾含量，单位依数据来源定义');
INSERT INTO `property_table` VALUES (214, 'dissolved_O_concentration', '溶解氧DO浓度，用于记录环境介质中溶解氧的浓度');
INSERT INTO `property_table` VALUES (215, 'dissolved_H_concentration', '溶解氢DH浓度，用于记录环境介质中溶解氢的浓度');
INSERT INTO `property_table` VALUES (216, 'crack_growth_rate', '裂纹扩展速率，用于描述裂纹在特定载荷和环境条件下随时间或循环数增长的速率');
INSERT INTO `property_table` VALUES (217, 'irradiation_source', '辐照源，用于记录材料辐照实验所采用的辐照粒子或辐照源类型，例如Fe离子、质子、中子等');
INSERT INTO `property_table` VALUES (218, 'irradiation_temperature', '辐照温度，用于记录材料在辐照过程中所处的温度条件，单位依数据来源定义，例如℃');
INSERT INTO `property_table` VALUES (219, 'irradiation_dose', '辐照剂量，用于记录材料辐照实验中的累积辐照损伤剂量，常见单位为dpa');
INSERT INTO `property_table` VALUES (220, 'indentation_depth', '压入深度，用于记录纳米压痕或压入测试过程中压头进入材料表面的深度，单位依数据来源定义');
INSERT INTO `property_table` VALUES (221, 'nanoindentation_hardness', '纳米压痕硬度，用于记录通过纳米压痕测试获得的材料硬度，常见单位为GPa');
INSERT INTO `property_table` VALUES (222, 'nanoindentation_modulus', '纳米压痕模量，用于记录通过纳米压痕测试获得的材料模量，常见单位为GPa');
INSERT INTO `property_table` VALUES (223, 'sample_code', '试样编号，用于记录具体测试样件、试样或实验记录中的编号标识，便于区分同一材料在不同处理状态、不同测试条件或不同批次下的样品，并支持数据追溯与关联管理');
INSERT INTO `property_table` VALUES (224, 'material_composition', '材料成分信息，用于记录材料中各元素及其含量组成，可包含质量分数、原子分数或配比描述，支持合金、复合材料及多组分体系的成分表达。');
INSERT INTO `property_table` VALUES (225, 'grain_average_width', '晶粒平均宽度，表示单个晶粒或显微组织特征单元在特定方向或截面上的平均宽度尺寸，常用于表征晶粒的形貌特征与尺度大小');
INSERT INTO `property_table` VALUES (226, 'ct_corrosion_potential', 'CT试样腐蚀电位，专门用于记录在高温高压水环境中，紧凑拉伸(CT)试样本体所测量到的原位开路电位');
INSERT INTO `property_table` VALUES (227, 'pt_corrosion_potential', 'PT电极腐蚀电位，专门用于记录实验环境中铂(Pt)电极或辅助探头测量到的溶液参考电位数据');
INSERT INTO `property_table` VALUES (228, 'gamma_prime_size', 'γ\'相尺寸，用于记录高温合金中主要强化相(γ\'相)的平均物理尺寸');
INSERT INTO `property_table` VALUES (229, 'hardness_hb', '布氏硬度HB，钛合金标准中常用的硬度表示方法');
INSERT INTO `property_table` VALUES (230, 'shear_modulus', '剪切模量(GPa)，描述材料抵抗剪切形变的能力');
INSERT INTO `property_table` VALUES (231, 'compressive_modulus', '压缩模量(GPa)，材料在受压状态下的弹性模量');
INSERT INTO `property_table` VALUES (232, 'fracture_toughness', '断裂韧度(MPa·m^1/2)，评价材料抵抗裂纹失稳扩展的关键指标');
INSERT INTO `property_table` VALUES (233, 'creep_rupture_strength', '持久强度(MPa)，材料在高温长时载荷下抵抗断裂的能力');
INSERT INTO `property_table` VALUES (234, 'product_category', '品种/类别说明，用于记录钛合金的品种（如板材、棒材）或所属类别');
INSERT INTO `property_table` VALUES (235, 'sample_type', '试样类型或形状描述，例如冲击试验中的U型缺口、V型缺口或拉伸试样类型标识');
INSERT INTO `property_table` VALUES (236, 'heat_treatment_batch', '热处理批次号或热处理号，用于追踪材料所经历的具体热处理制度记录');
INSERT INTO `property_table` VALUES (237, 'martensite_start_temperature', '马氏体转变开始温度(Ms)，表示奥氏体开始发生马氏体相变的临界温度，单位通常为℃');
INSERT INTO `property_table` VALUES (238, 'diffusion_layer_depth', '化学热处理扩散层深度，用于记录渗碳、渗氮、碳氮共渗等工艺形成的表面强化层深度，单位通常为mm');
INSERT INTO `property_table` VALUES (239, 'PA6T_copolymer_type', '	PA6T系共聚物的单体组合类型');
INSERT INTO `property_table` VALUES (240, 'pa6t_content', 'PA6T组分在共聚物中的质量百分比含量');
INSERT INTO `property_table` VALUES (241, 'temperature_range', '实验测试所覆盖的温度区间');
INSERT INTO `property_table` VALUES (242, 'density_range', '该温度区间内材料密度的变化范围');
INSERT INTO `property_table` VALUES (243, 'energy_range', '该温度区间内体系能量的变化范围');
INSERT INTO `property_table` VALUES (244, 'energy', '对应温度下体系的势能/总能量计算值');
INSERT INTO `property_table` VALUES (245, 'specimen_blank_diameter', '测试试样毛坯直径范围');

SET FOREIGN_KEY_CHECKS = 1;
