; ModuleID = 'original_prefix.bc'
source_filename = "orig_minimal_prefix.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@reached_NL = dso_local global i32 0, align 4, !dbg !0
@.str = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.1 = private unnamed_addr constant [22 x i8] c"orig_minimal_prefix.c\00", align 1
@__PRETTY_FUNCTION__.logic_bomb = private unnamed_addr constant [23 x i8] c"int logic_bomb(char *)\00", align 1
@.str.2 = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !13 {
entry:
  %retval = alloca i32, align 4
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !18, metadata !DIExpression()), !dbg !19
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !20, metadata !DIExpression()), !dbg !21
  %0 = load i8*, i8** %s.addr, align 8, !dbg !22
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !22
  %1 = load i8, i8* %arrayidx, align 1, !dbg !22
  %conv = sext i8 %1 to i32, !dbg !22
  %sub = sub nsw i32 %conv, 48, !dbg !23
  store i32 %sub, i32* %symvar, align 4, !dbg !21
  store i32 1, i32* @reached_NL, align 4, !dbg !24
  %call = call i32 (i8*, i8*, i32, i8*, ...) bitcast (i32 (...)* @__assert_fail to i32 (i8*, i8*, i32, i8*, ...)*)(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0), i8* getelementptr inbounds ([22 x i8], [22 x i8]* @.str.1, i64 0, i64 0), i32 15, i8* getelementptr inbounds ([23 x i8], [23 x i8]* @__PRETTY_FUNCTION__.logic_bomb, i64 0, i64 0)), !dbg !25
  call void @llvm.dbg.declare(metadata double* %d, metadata !26, metadata !DIExpression()), !dbg !28
  %2 = load i32, i32* %symvar, align 4, !dbg !29
  %conv1 = sitofp i32 %2 to double, !dbg !29
  %call2 = call double @log(double %conv1) #5, !dbg !30
  store double %call2, double* %d, align 8, !dbg !28
  %3 = load double, double* %d, align 8, !dbg !31
  %cmp = fcmp olt double 2.000000e+00, %3, !dbg !33
  br i1 %cmp, label %land.lhs.true, label %if.else, !dbg !34

land.lhs.true:                                    ; preds = %entry
  %4 = load double, double* %d, align 8, !dbg !35
  %cmp4 = fcmp olt double %4, 4.000000e+00, !dbg !36
  br i1 %cmp4, label %if.then, label %if.else, !dbg !37

if.then:                                          ; preds = %land.lhs.true
  store i32 1, i32* %retval, align 4, !dbg !38
  br label %return, !dbg !38

if.else:                                          ; preds = %land.lhs.true, %entry
  store i32 0, i32* %retval, align 4, !dbg !40
  br label %return, !dbg !40

return:                                           ; preds = %if.else, %if.then
  %5 = load i32, i32* %retval, align 4, !dbg !42
  ret i32 %5, !dbg !42
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: noreturn
declare dso_local i32 @__assert_fail(...) #2

; Function Attrs: nounwind
declare dso_local double @log(double) #3

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !43 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !46, metadata !DIExpression()), !dbg !50
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !51
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.2, i64 0, i64 0)), !dbg !52
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !53
  %0 = load i8, i8* %arrayidx, align 1, !dbg !53
  %conv = sext i8 %0 to i32, !dbg !53
  %cmp = icmp sge i32 %conv, 0, !dbg !54
  %conv1 = zext i1 %cmp to i32, !dbg !54
  %conv2 = sext i32 %conv1 to i64, !dbg !53
  call void @klee_assume(i64 %conv2), !dbg !55
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !56
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !57
  %1 = load i32, i32* @reached_NL, align 4, !dbg !58
  %conv4 = sext i32 %1 to i64, !dbg !58
  call void @klee_assume(i64 %conv4), !dbg !59
  ret i32 0, !dbg !60
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #4

declare dso_local void @klee_assume(i64) #4

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { noreturn "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #5 = { nounwind }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!7, !8, !9, !10, !11}
!llvm.ident = !{!12}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "reached_NL", scope: !2, file: !3, line: 8, type: !6, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C99, file: !3, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !4, globals: !5, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "orig_minimal_prefix.c", directory: "/home/klee")
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
!24 = !DILocation(line: 14, column: 16, scope: !13)
!25 = !DILocation(line: 15, column: 5, scope: !13)
!26 = !DILocalVariable(name: "d", scope: !13, file: !3, line: 16, type: !27)
!27 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!28 = !DILocation(line: 16, column: 12, scope: !13)
!29 = !DILocation(line: 16, column: 20, scope: !13)
!30 = !DILocation(line: 16, column: 16, scope: !13)
!31 = !DILocation(line: 18, column: 12, scope: !32)
!32 = distinct !DILexicalBlock(scope: !13, file: !3, line: 18, column: 8)
!33 = !DILocation(line: 18, column: 10, scope: !32)
!34 = !DILocation(line: 18, column: 14, scope: !32)
!35 = !DILocation(line: 18, column: 17, scope: !32)
!36 = !DILocation(line: 18, column: 19, scope: !32)
!37 = !DILocation(line: 18, column: 8, scope: !13)
!38 = !DILocation(line: 19, column: 9, scope: !39)
!39 = distinct !DILexicalBlock(scope: !32, file: !3, line: 18, column: 23)
!40 = !DILocation(line: 21, column: 9, scope: !41)
!41 = distinct !DILexicalBlock(scope: !32, file: !3, line: 20, column: 10)
!42 = !DILocation(line: 23, column: 1, scope: !13)
!43 = distinct !DISubprogram(name: "main", scope: !3, file: !3, line: 25, type: !44, scopeLine: 25, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!44 = !DISubroutineType(types: !45)
!45 = !{!6}
!46 = !DILocalVariable(name: "s", scope: !43, file: !3, line: 26, type: !47)
!47 = !DICompositeType(tag: DW_TAG_array_type, baseType: !17, size: 32, elements: !48)
!48 = !{!49}
!49 = !DISubrange(count: 4)
!50 = !DILocation(line: 26, column: 10, scope: !43)
!51 = !DILocation(line: 27, column: 24, scope: !43)
!52 = !DILocation(line: 27, column: 5, scope: !43)
!53 = !DILocation(line: 29, column: 17, scope: !43)
!54 = !DILocation(line: 29, column: 22, scope: !43)
!55 = !DILocation(line: 29, column: 5, scope: !43)
!56 = !DILocation(line: 30, column: 16, scope: !43)
!57 = !DILocation(line: 30, column: 5, scope: !43)
!58 = !DILocation(line: 31, column: 17, scope: !43)
!59 = !DILocation(line: 31, column: 5, scope: !43)
!60 = !DILocation(line: 32, column: 5, scope: !43)
