; ModuleID = 'reachable_line_klee.bc'
source_filename = "reachable_line_klee.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@reached_NL = dso_local global i32 0, align 4, !dbg !0
@.str = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !13 {
entry:
  %retval = alloca i32, align 4
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca i32, align 4
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !18, metadata !DIExpression()), !dbg !19
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !20, metadata !DIExpression()), !dbg !21
  %0 = load i8*, i8** %s.addr, align 8, !dbg !22
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !22
  %1 = load i8, i8* %arrayidx, align 1, !dbg !22
  %conv = sext i8 %1 to i32, !dbg !22
  %sub = sub nsw i32 %conv, 48, !dbg !23
  store i32 %sub, i32* %symvar, align 4, !dbg !21
  call void @llvm.dbg.declare(metadata i32* %d, metadata !24, metadata !DIExpression()), !dbg !25
  %2 = load i32, i32* %symvar, align 4, !dbg !26
  store i32 %2, i32* %d, align 4, !dbg !25
  %3 = load i32, i32* %d, align 4, !dbg !27
  %cmp = icmp slt i32 2, %3, !dbg !29
  br i1 %cmp, label %land.lhs.true, label %if.else, !dbg !30

land.lhs.true:                                    ; preds = %entry
  %4 = load i32, i32* %d, align 4, !dbg !31
  %cmp2 = icmp slt i32 %4, 4, !dbg !32
  br i1 %cmp2, label %if.then, label %if.else, !dbg !33

if.then:                                          ; preds = %land.lhs.true
  store i32 1, i32* @reached_NL, align 4, !dbg !34
  store i32 1, i32* %retval, align 4, !dbg !36
  br label %return, !dbg !36

if.else:                                          ; preds = %land.lhs.true, %entry
  store i32 0, i32* %retval, align 4, !dbg !37
  br label %return, !dbg !37

return:                                           ; preds = %if.else, %if.then
  %5 = load i32, i32* %retval, align 4, !dbg !39
  ret i32 %5, !dbg !39
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !40 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !43, metadata !DIExpression()), !dbg !47
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !48
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0)), !dbg !49
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !50
  %0 = load i8, i8* %arrayidx, align 1, !dbg !50
  %conv = sext i8 %0 to i32, !dbg !50
  %cmp = icmp sge i32 %conv, 0, !dbg !51
  %conv1 = zext i1 %cmp to i32, !dbg !51
  %conv2 = sext i32 %conv1 to i64, !dbg !50
  call void @klee_assume(i64 %conv2), !dbg !52
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !53
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !54
  %1 = load i32, i32* @reached_NL, align 4, !dbg !55
  %tobool = icmp ne i32 %1, 0, !dbg !55
  br i1 %tobool, label %if.end, label %if.then, !dbg !57

if.then:                                          ; preds = %entry
  call void @klee_silent_exit(i32 0) #4, !dbg !58
  unreachable, !dbg !58

if.end:                                           ; preds = %entry
  ret i32 0, !dbg !59
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #2

declare dso_local void @klee_assume(i64) #2

; Function Attrs: noreturn
declare dso_local void @klee_silent_exit(i32) #3

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { noreturn "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { noreturn }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!7, !8, !9, !10, !11}
!llvm.ident = !{!12}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "reached_NL", scope: !2, file: !3, line: 8, type: !6, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C99, file: !3, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !4, globals: !5, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "reachable_line_klee.c", directory: "/home/klee")
!4 = !{}
!5 = !{!0}
!6 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!7 = !{i32 7, !"Dwarf Version", i32 4}
!8 = !{i32 2, !"Debug Info Version", i32 3}
!9 = !{i32 1, !"wchar_size", i32 4}
!10 = !{i32 7, !"uwtable", i32 1}
!11 = !{i32 7, !"frame-pointer", i32 2}
!12 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!13 = distinct !DISubprogram(name: "logic_bomb", scope: !3, file: !3, line: 11, type: !14, scopeLine: 11, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!14 = !DISubroutineType(types: !15)
!15 = !{!6, !16}
!16 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !17, size: 64)
!17 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!18 = !DILocalVariable(name: "s", arg: 1, scope: !13, file: !3, line: 11, type: !16)
!19 = !DILocation(line: 11, column: 22, scope: !13)
!20 = !DILocalVariable(name: "symvar", scope: !13, file: !3, line: 12, type: !6)
!21 = !DILocation(line: 12, column: 9, scope: !13)
!22 = !DILocation(line: 12, column: 18, scope: !13)
!23 = !DILocation(line: 12, column: 23, scope: !13)
!24 = !DILocalVariable(name: "d", scope: !13, file: !3, line: 14, type: !6)
!25 = !DILocation(line: 14, column: 5, scope: !13)
!26 = !DILocation(line: 14, column: 9, scope: !13)
!27 = !DILocation(line: 16, column: 12, scope: !28)
!28 = distinct !DILexicalBlock(scope: !13, file: !3, line: 16, column: 8)
!29 = !DILocation(line: 16, column: 10, scope: !28)
!30 = !DILocation(line: 16, column: 14, scope: !28)
!31 = !DILocation(line: 16, column: 17, scope: !28)
!32 = !DILocation(line: 16, column: 19, scope: !28)
!33 = !DILocation(line: 16, column: 8, scope: !13)
!34 = !DILocation(line: 17, column: 20, scope: !35)
!35 = distinct !DILexicalBlock(scope: !28, file: !3, line: 16, column: 23)
!36 = !DILocation(line: 18, column: 9, scope: !35)
!37 = !DILocation(line: 20, column: 9, scope: !38)
!38 = distinct !DILexicalBlock(scope: !28, file: !3, line: 19, column: 10)
!39 = !DILocation(line: 22, column: 1, scope: !13)
!40 = distinct !DISubprogram(name: "main", scope: !3, file: !3, line: 24, type: !41, scopeLine: 24, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!41 = !DISubroutineType(types: !42)
!42 = !{!6}
!43 = !DILocalVariable(name: "s", scope: !40, file: !3, line: 25, type: !44)
!44 = !DICompositeType(tag: DW_TAG_array_type, baseType: !17, size: 32, elements: !45)
!45 = !{!46}
!46 = !DISubrange(count: 4)
!47 = !DILocation(line: 25, column: 10, scope: !40)
!48 = !DILocation(line: 26, column: 24, scope: !40)
!49 = !DILocation(line: 26, column: 5, scope: !40)
!50 = !DILocation(line: 28, column: 17, scope: !40)
!51 = !DILocation(line: 28, column: 22, scope: !40)
!52 = !DILocation(line: 28, column: 5, scope: !40)
!53 = !DILocation(line: 29, column: 16, scope: !40)
!54 = !DILocation(line: 29, column: 5, scope: !40)
!55 = !DILocation(line: 30, column: 10, scope: !56)
!56 = distinct !DILexicalBlock(scope: !40, file: !3, line: 30, column: 9)
!57 = !DILocation(line: 30, column: 9, scope: !40)
!58 = !DILocation(line: 30, column: 22, scope: !56)
!59 = !DILocation(line: 31, column: 5, scope: !40)
