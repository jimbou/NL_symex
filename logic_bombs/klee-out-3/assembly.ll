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
  %d2 = alloca double, align 8
  %d5 = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !18, metadata !DIExpression()), !dbg !19
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !20, metadata !DIExpression()), !dbg !21
  %0 = load i8*, i8** %s.addr, align 8, !dbg !22
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !22
  %1 = load i8, i8* %arrayidx, align 1, !dbg !22
  %conv = sext i8 %1 to i32, !dbg !22
  %sub = sub nsw i32 %conv, 48, !dbg !23
  store i32 %sub, i32* %symvar, align 4, !dbg !21
  call void @llvm.dbg.declare(metadata double* %d, metadata !24, metadata !DIExpression()), !dbg !26
  %2 = load i32, i32* %symvar, align 4, !dbg !27
  %cmp = icmp slt i32 %2, 0, !dbg !29
  br i1 %cmp, label %if.then, label %if.else, !dbg !30

if.then:                                          ; preds = %entry
  store i32 1, i32* @reached_NL, align 4, !dbg !31
  %call = call i32 (i8*, i8*, i32, i8*, ...) bitcast (i32 (...)* @__assert_fail to i32 (i8*, i8*, i32, i8*, ...)*)(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0), i8* getelementptr inbounds ([22 x i8], [22 x i8]* @.str.1, i64 0, i64 0), i32 18, i8* getelementptr inbounds ([23 x i8], [23 x i8]* @__PRETTY_FUNCTION__.logic_bomb, i64 0, i64 0)), !dbg !33
  call void @llvm.dbg.declare(metadata double* %d2, metadata !34, metadata !DIExpression()), !dbg !35
  %3 = load i32, i32* %symvar, align 4, !dbg !36
  %conv3 = sitofp i32 %3 to double, !dbg !36
  %call4 = call double @log(double %conv3) #5, !dbg !37
  store double %call4, double* %d2, align 8, !dbg !35
  br label %if.end, !dbg !38

if.else:                                          ; preds = %entry
  call void @llvm.dbg.declare(metadata double* %d5, metadata !39, metadata !DIExpression()), !dbg !41
  store double 1.000000e+00, double* %d5, align 8, !dbg !41
  br label %if.end

if.end:                                           ; preds = %if.else, %if.then
  %4 = load double, double* %d, align 8, !dbg !42
  %cmp6 = fcmp olt double 2.000000e+00, %4, !dbg !44
  br i1 %cmp6, label %land.lhs.true, label %if.else11, !dbg !45

land.lhs.true:                                    ; preds = %if.end
  %5 = load double, double* %d, align 8, !dbg !46
  %cmp8 = fcmp olt double %5, 4.000000e+00, !dbg !47
  br i1 %cmp8, label %if.then10, label %if.else11, !dbg !48

if.then10:                                        ; preds = %land.lhs.true
  store i32 1, i32* %retval, align 4, !dbg !49
  br label %return, !dbg !49

if.else11:                                        ; preds = %land.lhs.true, %if.end
  store i32 0, i32* %retval, align 4, !dbg !51
  br label %return, !dbg !51

return:                                           ; preds = %if.else11, %if.then10
  %6 = load i32, i32* %retval, align 4, !dbg !53
  ret i32 %6, !dbg !53
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: noreturn
declare dso_local i32 @__assert_fail(...) #2

; Function Attrs: nounwind
declare dso_local double @log(double) #3

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !54 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !57, metadata !DIExpression()), !dbg !61
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !62
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.2, i64 0, i64 0)), !dbg !63
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !64
  %0 = load i8, i8* %arrayidx, align 1, !dbg !64
  %conv = sext i8 %0 to i32, !dbg !64
  %cmp = icmp sge i32 %conv, 0, !dbg !65
  %conv1 = zext i1 %cmp to i32, !dbg !65
  %conv2 = sext i32 %conv1 to i64, !dbg !64
  call void @klee_assume(i64 %conv2), !dbg !66
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !67
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !68
  %1 = load i32, i32* @reached_NL, align 4, !dbg !69
  %conv4 = sext i32 %1 to i64, !dbg !69
  call void @klee_assume(i64 %conv4), !dbg !70
  ret i32 0, !dbg !71
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
!24 = !DILocalVariable(name: "d", scope: !13, file: !3, line: 13, type: !25)
!25 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!26 = !DILocation(line: 13, column: 12, scope: !13)
!27 = !DILocation(line: 14, column: 9, scope: !28)
!28 = distinct !DILexicalBlock(scope: !13, file: !3, line: 14, column: 9)
!29 = !DILocation(line: 14, column: 16, scope: !28)
!30 = !DILocation(line: 14, column: 9, scope: !13)
!31 = !DILocation(line: 17, column: 16, scope: !32)
!32 = distinct !DILexicalBlock(scope: !28, file: !3, line: 14, column: 21)
!33 = !DILocation(line: 18, column: 5, scope: !32)
!34 = !DILocalVariable(name: "d", scope: !32, file: !3, line: 19, type: !25)
!35 = !DILocation(line: 19, column: 12, scope: !32)
!36 = !DILocation(line: 19, column: 20, scope: !32)
!37 = !DILocation(line: 19, column: 16, scope: !32)
!38 = !DILocation(line: 20, column: 5, scope: !32)
!39 = !DILocalVariable(name: "d", scope: !40, file: !3, line: 22, type: !25)
!40 = distinct !DILexicalBlock(scope: !28, file: !3, line: 21, column: 9)
!41 = !DILocation(line: 22, column: 16, scope: !40)
!42 = !DILocation(line: 25, column: 12, scope: !43)
!43 = distinct !DILexicalBlock(scope: !13, file: !3, line: 25, column: 8)
!44 = !DILocation(line: 25, column: 10, scope: !43)
!45 = !DILocation(line: 25, column: 14, scope: !43)
!46 = !DILocation(line: 25, column: 17, scope: !43)
!47 = !DILocation(line: 25, column: 19, scope: !43)
!48 = !DILocation(line: 25, column: 8, scope: !13)
!49 = !DILocation(line: 26, column: 9, scope: !50)
!50 = distinct !DILexicalBlock(scope: !43, file: !3, line: 25, column: 23)
!51 = !DILocation(line: 28, column: 9, scope: !52)
!52 = distinct !DILexicalBlock(scope: !43, file: !3, line: 27, column: 10)
!53 = !DILocation(line: 30, column: 1, scope: !13)
!54 = distinct !DISubprogram(name: "main", scope: !3, file: !3, line: 32, type: !55, scopeLine: 32, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!55 = !DISubroutineType(types: !56)
!56 = !{!6}
!57 = !DILocalVariable(name: "s", scope: !54, file: !3, line: 33, type: !58)
!58 = !DICompositeType(tag: DW_TAG_array_type, baseType: !17, size: 32, elements: !59)
!59 = !{!60}
!60 = !DISubrange(count: 4)
!61 = !DILocation(line: 33, column: 10, scope: !54)
!62 = !DILocation(line: 34, column: 24, scope: !54)
!63 = !DILocation(line: 34, column: 5, scope: !54)
!64 = !DILocation(line: 36, column: 17, scope: !54)
!65 = !DILocation(line: 36, column: 22, scope: !54)
!66 = !DILocation(line: 36, column: 5, scope: !54)
!67 = !DILocation(line: 37, column: 16, scope: !54)
!68 = !DILocation(line: 37, column: 5, scope: !54)
!69 = !DILocation(line: 38, column: 17, scope: !54)
!70 = !DILocation(line: 38, column: 5, scope: !54)
!71 = !DILocation(line: 39, column: 5, scope: !54)
