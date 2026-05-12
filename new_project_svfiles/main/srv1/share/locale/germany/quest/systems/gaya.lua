quest gaya begin
	state start begin
		when 20504.chat."Gaya Shop" begin
			cmdchat("GemOpen")
			setskin(0)
		end
		when 20503.chat."Create Gaya" begin
			local x = select("Create Gaya (1)", "Create Gaya (5)", "Create Gaya (10)", "Create Gaya (25)", "Create Gaya (50)", "Create max. Gaya", "Cancel")
			if x >= 1 and x <= 6 then
				say_title(mob_name(20503))
				local pieceList = {1,5,10,25,50,200}
				local getCountStone = pc.count_item(30401)
				if getCountStone > pieceList[x] then
					getCountStone = pieceList[x]
				end
				local gemstonesCount = math.floor(pc.count_item(30400) / 10)
				local gold = math.floor(pc.get_gold() / 500000)
				local lowerValue = 0
				if gemstonesCount < getCountStone and gemstonesCount < gold then
					lowerValue = gemstonesCount
				elseif getCountStone < gemstonesCount and getCountStone < gold then
					lowerValue = getCountStone
				elseif gold < gemstonesCount and gold < getCountStone then
					lowerValue = gold
				else
					if getCountStone > 0 and gemstonesCount > 0 and gold > 0 then
						lowerValue = 1
					end
				end
				if lowerValue == 0 then
					say("To make 1 Gaya you need:")
					say("10 Gemstones")
					say("1 Piece of Gaya")
					say("500.000 Yang")
					return
				end
				say("You need make for "..lowerValue.." for gaya:")
				say(""..(lowerValue*10).." Gemstones")
				say(""..lowerValue.." Piece Of Gaya")
				say(""..(lowerValue*500000).." Yang")
				say("Do you want make "..lowerValue.." gaya?")
				local q = select("Yes", "Cancel")
				if q == 1 then
					pc.remove_item(30401, lowerValue)
					pc.remove_item(30400, lowerValue*10)
					pc.change_gold(-(lowerValue*500000))
					syschat("Succesfully gaya creating "..lowerValue)
					pc.change_gem(lowerValue)
				end
			end
		end
		when 20503.chat."Create Piece of Gaya" begin
			local x = select("Create Piece of Gaya (1)", "Create Piece of Gaya (5)", "Create Piece of Gaya (10)", "Create Piece of Gaya (25)", "Create Piece of Gaya (50)", "Create max. Piece of Gaya", "Cancel")
			if x >= 1 and x <= 6 then
				say_title(mob_name(20503))
				local pieceList = {1*2,5*2,10*2,25*2,50*2,200*2}
				local selectedPiece = pieceList[x]
				local getCountStone = pc.calculate_gaya_piece(selectedPiece, true)
				if getCountStone == 0 then
					say("To make 1 Piece of Gaya you need:")
					say("2 Spirit Stones +0 to +3")
					say("")
					say("Come back when you have enought Spirit Stones.")
					return
				end
				say("You need make for "..(getCountStone/2).." for gaya piece:")
				say(""..getCountStone.." Soul stone need +0-+3")
				say("")
				say("Do you want make "..(getCountStone/2).." gaya piece?")
				local q = select("Yes", "Cancel")
				if q == 1 then
					local makeCount = pc.calculate_gaya_piece(selectedPiece, false)
					syschat("Succesfully gaya piece creating "..(makeCount/2))
					if makeCount > 0 then
						pc.give_item2(30401, makeCount/2)
					end
				end
			end
		end

		when 30402.use begin
			pc.change_gem(1)
			syschat("Added 1 gaya point in your character.")
			item.set_count(item.get_count()-1)
		end
		when 30403.use begin
			pc.change_gem(5)
			syschat("Added 5 gaya point in your character.")
			item.set_count(item.get_count()-1)
		end
		when 30404.use begin
			pc.change_gem(10)
			syschat("Added 10 gaya point in your character.")
			item.set_count(item.get_count()-1)
		end
		when 30405.use begin
			pc.change_gem(15)
			syschat("Added 15 gaya point in your character.")
			item.set_count(item.get_count()-1)
		end
		when 30406.use begin
			pc.change_gem(25)
			syschat("Added 25 gaya point in your character.")
			item.set_count(item.get_count()-1)
		end
		when 30407.use begin
			pc.change_gem(50)
			syschat("Added 50 gaya point in your character.")
			item.set_count(item.get_count()-1)
		end
		when 30408.use begin
			pc.change_gem(100)
			syschat("Added 100 gem point in your character.")
			item.set_count(item.get_count()-1)
		end
	end
end
