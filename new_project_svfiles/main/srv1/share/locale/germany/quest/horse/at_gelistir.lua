quest binek_gelistir begin
	state start begin
		function get_madalyon_info(gorev_level)
			if binek_gelistir.madalyon_info==nil then
				binek_gelistir.madalyon_info = {
					-- itemvnum - toplam edet - efsun - level - sans - sure - ruhtasi
					[2] = {"100.000", 1, 100000},
					[3] = {"100.000", 1, 100000},
					[4] = {"100.000", 1, 100000},
					[5] = {"100.000", 1, 100000},
					[6] = {"100.000", 1, 100000},
					[7] = {"100.000", 1, 100000},
					[8] = {"100.000", 1, 100000},
					[9] = {"100.000", 1, 100000},
					[10] = {"100.000", 1, 100000},
					[11] = {"100.000", 1, 100000},
					[12] = {"1.000.000", 1, 1000000},
					[13] = {"1.000.000", 1, 1000000},
					[14] = {"1.000.000", 1, 1000000},
					[15] = {"1.000.000", 1, 1000000},
					[16] = {"1.000.000", 1, 1000000},
					[17] = {"1.000.000", 1, 1000000},
					[18] = {"1.000.000", 1, 1000000},
					[19] = {"1.000.000", 1, 1000000},
					[20] = {"1.000.000", 1, 1000000},
					[21] = {"5.000.000", 10, 5000000},
					[22] = {"0", 0, 0},
					--[22] = {"500.000", 1, 500000},
					--[23] = {"500.000", 1, 500000},
					--[24] = {"500.000", 1, 500000},
					--[25] = {"500.000", 1, 500000},
					--[26] = {"500.000", 1, 500000},
					--[27] = {"500.000", 1, 500000},
					--[28] = {"500.000", 1, 500000},
					--[29] = {"500.000", 1, 500000},
					--[30] = {"500.000", 1, 500000},
					--[31] = {"0", 0, 0},
				}
			end
			return binek_gelistir.madalyon_info[gorev_level]
		end
		
		when 20349.chat."Atýmý geliþtir" begin
			local level = horse.get_level()
			local level2 = level+1
			local madalyon_info = binek_gelistir.get_madalyon_info(level2)
			local gereken_yang = madalyon_info[1]
			local gereken_madalyon = madalyon_info[2]
			local gereken_yang2 = madalyon_info[3]
			
			if level >= 21 then
				say_title("Seyis: ")
				say("")
				say_reward("Atýn max. seviyeye ulaþmýþ. ")
				return
			end
			say_title("Seyis ")
			say("Demek Atýný geliþtirmek istiyorsun.. ")
			say_reward("Binicilik Seviyesi: "..level)
			say_reward("Sonraki Seviye: "..level2)
			raw_script("[TEXT_HORIZONTAL_ALIGN_CENTER]") say_reward("- Gerekenler - ")
			say_item_vnum(50050)
			raw_script("[TEXT_HORIZONTAL_ALIGN_CENTER]") say(": "..gereken_yang.." Yang")
			say("")
			local var = select("Atýmý geliþtir ", "Kapat ")
			if var == 1 then
				if pc.count_item(50050) < gereken_madalyon then
					say_title("Seyis ")
					say("")
					say("Gerekli eþya "..gereken_madalyon.."x: "..item_name(50050)..": ")
					say_item_vnum(50050)
					return
				end
				if pc.get_gold() < gereken_yang2 then
					say_title("Seyis ")
					say("")
					say("Üzerinde yeterli yang yok. ")
					return
				end
				say_title("Seyis ")
				say("")
				say_reward("Tebrikler! Atýn seviye atladý. ")
				pc.change_gold(-gereken_yang2)
				pc.remove_item(50050,gereken_madalyon)
				horse.advance()
			else
				return
			end
		end
	end
end